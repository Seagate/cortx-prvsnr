#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging
from copy import deepcopy
import ipaddress
import functools
from typing import List, Union, Any, Iterable, Tuple, Dict
from pathlib import Path

from . import config
from .vendor import attr
from .errors import UnknownParamError, SWUpdateRepoSourceError
from .pillar import (
    KeyPath, PillarKeyAPI, PillarKey, PillarItemsAPI
)
from .param import Param, ParamDictItem
from .api_spec import param_spec
from .values import (
    UNDEFINED, UNCHANGED, NONE, value_from_str,
    is_special
)
from .serialize import PrvsnrType, loads
from .utils import load_yaml

cli_spec = load_yaml(config.CLI_SPEC_PATH)

METADATA_PARAM_GROUP_KEY = '_param_group_key'
METADATA_ARGPARSER = '_param_argparser'

logger = logging.getLogger(__name__)


# TODO IMPROVE use some attr api to copy spec
def copy_attr(_attr, name=None, **changes):
    attr_kw = {}
    for arg in (
        'default', 'validator', 'repr', 'hash',
        'init', 'metadata', 'type', 'converter', 'kw_only'
    ):
        attr_kw[arg] = (
            changes[arg] if arg in changes else getattr(_attr, arg)
        )

    if not name:
        name = _attr.name

    _utility_type = attr.make_class(
        "_UtilityType", {
            name: attr.ib(**attr_kw)
        }
    )

    return attr.fields_dict(_utility_type)[name]


@attr.s(auto_attribs=True)
class AttrParserArgs:
    _attr: Any  # TODO typing
    prefix: str = attr.ib(default=None)

    name: str = attr.ib(init=False, default=None)
    action: str = attr.ib(init=False, default='store')
    metavar: str = attr.ib(init=False, default=None)
    dest: str = attr.ib(init=False, default=None)
    default: str = attr.ib(init=False, default=None)
    const: str = attr.ib(init=False, default=None)
    choices: List = attr.ib(init=False, default=None)
    help: str = attr.ib(init=False, default='')
    type: Any = attr.ib(init=False, default=None)  # TODO typing
    # TODO TEST EOS-8473
    nargs: str = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):  # noqa: C901 FIXME
        self.name = self._attr.name

        if self.name.startswith('__'):
            raise ValueError(
                f"{self.name}: multiple leading underscores are not expected"
            )

        self.name = self.name.lstrip('_')

        if self.prefix:
            self.name = self.prefix + self.name

        parser_args = {}

        parser_args = self._attr.metadata.get(
            METADATA_ARGPARSER, {}
        )

        if parser_args.get('choices'):
            self.choices = parser_args.get('choices')

        if parser_args.get('action'):
            self.action = parser_args.get('action')
        elif self._attr.type is bool:
            self.action = 'store_true'

        self.type = parser_args.get(
            'type',
            functools.partial(
                self.value_from_str, v_type=self._attr.type
            )
        )

        for arg in ('help', 'dest', 'const'):
            if arg in parser_args:
                setattr(self, arg, parser_args.get(arg))

        if self.choices:
            self.help = (
                '{} [choices: {}]'
                .format(self.help, ', '.join(self.choices))
            )

        # TODO TEST EOS-8473
        if parser_args.get('nargs'):
            self.nargs = parser_args.get('nargs')

        if self._attr.default is not attr.NOTHING:
            # optional argument
            self.name = '--' + self.name.replace('_', '-')
            # default value for an object (attr) might be more
            # complicated than for a parser
            default_v = parser_args.get('default', self._attr.default)
            if isinstance(default_v, attr.Factory):
                default_v = default_v.factory()
            self.default = default_v
            self.metavar = parser_args.get('metavar')
            if not self.metavar and self._attr.type:
                self.metavar = getattr(self._attr.type, '__name__', None)
            if self.metavar:
                self.metavar = self.metavar.upper()

    @property
    def kwargs(self):
        def _filter(_attr, value):
            not_filter = ['_attr', 'name', 'prefix']
            if self.action in ('store_true', 'store_false'):
                not_filter.extend(['metavar', 'type', 'default'])
            if self.action in ('store_const',):
                not_filter.extend(['type'])
            # TODO TEST EOS-8473 nargs
            for arg in ('choices', 'dest', 'const', 'nargs'):
                if getattr(self, arg) is None:
                    not_filter.append(arg)
            return _attr.name not in not_filter

        return attr.asdict(self, filter=_filter)

    @classmethod
    def value_from_str(cls, value, v_type=None):
        _value = value_from_str(value)
        if _value is NONE:
            _value = None
        elif isinstance(_value, str):
            if (v_type is List) or (v_type == 'json'):
                _value = loads(value)
        return _value


class InputAttrParserArgs(AttrParserArgs):
    @classmethod
    def value_from_str(cls, value, v_type=None):
        _value = super().value_from_str(value, v_type=v_type)
        return UNCHANGED if _value is None else _value


class ParserFiller:
    @staticmethod
    def fill_parser(cls, parser, attr_parser_cls=AttrParserArgs):
        for _attr in attr.fields(cls):
            if METADATA_ARGPARSER in _attr.metadata:
                parser_prefix = getattr(cls, 'parser_prefix', None)
                metadata = _attr.metadata[METADATA_ARGPARSER]

                if isinstance(metadata, str):
                    metadata = KeyPath(metadata).value(cli_spec)

                if metadata.get('action') == 'store_bool':
                    for name, default, m_changes in (
                        (_attr.name, _attr.default, {
                            'help': f"enable {metadata['help']}",
                            'action': 'store_const',
                            'const': True,
                            'dest': _attr.name,
                        }), (f'no{_attr.name}', not _attr.default, {
                            'help': f"disable {metadata['help']}",
                            'action': 'store_const',
                            'const': False,
                            'dest': _attr.name,
                        })
                    ):
                        metadata_copy = deepcopy(metadata)
                        metadata_copy.update(m_changes)
                        attr_copy = copy_attr(
                            _attr, name=name, default=default, metadata={
                                METADATA_ARGPARSER: metadata_copy
                            }
                        )
                        args = attr_parser_cls(attr_copy, prefix=parser_prefix)
                        parser.add_argument(args.name, **args.kwargs)
                else:
                    args = attr_parser_cls(_attr, prefix=parser_prefix)
                    parser.add_argument(args.name, **args.kwargs)

    @staticmethod
    def extract_positional_args(cls, kwargs):
        _args = []
        for _attr in attr.fields(cls):
            if METADATA_ARGPARSER in _attr.metadata:
                if _attr.default is attr.NOTHING and _attr.name in kwargs:
                    _args.append(kwargs.pop(_attr.name))
        return _args, kwargs


@attr.s(auto_attribs=True)
class NoParams:
    @classmethod
    def fill_parser(cls, parser):
        pass

    @classmethod
    def extract_positional_args(cls, kwargs):
        return (), kwargs


@attr.s(auto_attribs=True, frozen=True)
class PillarKeysList:
    _keys: List[PillarKey] = attr.Factory(list)

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    @classmethod
    def from_args(
        cls,
        *args: Tuple[Union[str, Tuple[str, str]], ...]
    ):
        pi_keys = []
        for arg in args:
            if type(arg) is str:
                pi_keys.append(PillarKey(arg))
            elif type(arg) is tuple:
                # TODO IMPROVE more checks for tuple types and len
                pi_keys.append(PillarKey(*arg))
            else:
                raise TypeError(f"Unexpected type {type(arg)} of args {arg}")
        return cls(pi_keys)

    @classmethod
    def fill_parser(cls, parser):
        parser.add_argument(
            'args', metavar='keypath', type=str, nargs='*',
            help='a pillar key path'
        )

    @classmethod
    def extract_positional_args(cls, kwargs):
        return (), kwargs


@attr.s(auto_attribs=True, frozen=True)
class PillarInputBase(PillarItemsAPI):
    keypath: str = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': 'pillar key path',
                # 'metavar': 'value'
            }
        }
    )
    # TODO IMPROVE use some constant for json type
    value: Any = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': 'pillar value',
                'type': functools.partial(
                    AttrParserArgs.value_from_str, v_type='json'
                )
                # 'metavar': 'value'
            }
        }
    )
    fpath: str = attr.ib(
        default=None,
        metadata={
            METADATA_ARGPARSER: {
                'help': (
                    'file path relative to pillar roots, '
                    'if not specified <key-path-top-level-part>.sls is used'
                ),
                # 'metavar': 'value'
            }
        }
    )

    def pillar_items(self) -> Iterable[Tuple[PillarKeyAPI, Any]]:
        return (
            (PillarKey(self.keypath, self.fpath), self.value),
        )

    @classmethod
    def from_args(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fill_parser(cls, parser):
        ParserFiller.fill_parser(cls, parser, AttrParserArgs)

    @classmethod
    def extract_positional_args(cls, kwargs):
        return ParserFiller.extract_positional_args(cls, kwargs)


@attr.s(auto_attribs=True)
class ParamsList:
    params: List[Param]

    def __iter__(self):
        return iter(self.params)

    @classmethod
    def from_args(cls, *args: List[Union[str, Param]]):
        params = []
        for param in args:
            key_path = KeyPath(str(param))
            param = param_spec.get(str(key_path))
            if param is None:
                param_di = param_spec.get(str(key_path.parent))
                if isinstance(param_di, ParamDictItem):
                    param = Param(
                        key_path,
                        (param_di.keypath / key_path.leaf, param_di.fpath)
                    )
                else:
                    logger.error(
                        "Unknown param {}".format(key_path)
                    )
                    raise UnknownParamError(str(key_path))
            params.append(param)
        return cls(params)

    @classmethod
    def fill_parser(cls, parser):
        parser.add_argument(
            'args', metavar='param', type=str, nargs='+',
            help='a param name to get'
        )

    @classmethod
    def extract_positional_args(cls, kwargs):
        return (), kwargs


class ParamGroupInputBase(PillarItemsAPI):
    _param_group = None
    _spec = None

    def pillar_items(self):  # TODO return type
        res = {}
        for attr_name in attr.fields_dict(type(self)):
            res[self.param_spec(attr_name)] = getattr(self, attr_name)
        return iter(res.items())

    @classmethod
    def param_spec(cls, attr_name: str):
        if cls._spec is None:
            cls._spec = {}
        if attr_name not in cls._spec:
            try:
                _attr = attr.fields_dict(cls)[attr_name]
            except KeyError:
                logger.error("unknown attr {}".format(attr_name))
                raise ValueError('unknown attr {}'.format(attr_name))
            else:
                # TODO TEST
                param_group = _attr.metadata.get(METADATA_PARAM_GROUP_KEY, '')
                full_path = (
                    "{}/{}".format(param_group, attr_name) if param_group
                    else attr_name
                )
                cls._spec[attr_name] = param_spec[full_path]
        return cls._spec[attr_name]

    @classmethod
    def from_args(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fill_parser(cls, parser):
        ParserFiller.fill_parser(cls, parser, InputAttrParserArgs)

    @classmethod
    def extract_positional_args(cls, kwargs):
        return ParserFiller.extract_positional_args(cls, kwargs)

    @staticmethod
    def _attr_ib(
        param_group='', default=UNCHANGED, descr='', metavar=None, **kwargs
    ):
        return attr.ib(
            default=default,
            metadata={
                METADATA_PARAM_GROUP_KEY: param_group,
                METADATA_ARGPARSER: {
                    'help': descr,
                    'metavar': metavar
                }
            },
            **kwargs
        )


class Validation():
    @staticmethod
    def check_ip4(instace, attribute, value):
        try:
            ip = None
            if value and value != UNCHANGED and value != 'None':  # FIXME JBOD
                ip = ipaddress.IPv4Address(value)
                # TODO : Improve logic internally convert ip to
                # canonical forms.
                if str(ip) != value:
                    raise ValueError(
                        "IP is not in canonical form."
                        f"Canonical form of IP can be {str(ip)}"
                    )
        except ValueError as exc:
            raise ValueError(
                f"{attribute.name}: invalid ip4 address {value} "
                f"Error: {str(exc)}"
            )


@attr.s(auto_attribs=True)
class NTP(ParamGroupInputBase):
    _param_group = 'ntp'
    # TODO some trick to avoid passing that value
    server: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="ntp server ip"
    )
    timezone: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="ntp server timezone"
    )


class ReleaseParams():
    _param_group = 'release'
    target_build: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Cortx deployment build"
    )


@attr.s(auto_attribs=True)
class Release(ParamGroupInputBase):
    target_build: str = ReleaseParams.target_build


class StorageEnclosureParams():
    _param_group = 'storage'
    enclosure_id: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="Enclosure ID"
    )
    type: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Type of storage"
    )
    primary_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Controller A IP",
        validator=Validation.check_ip4
    )
    secondary_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Controller B IP",
        validator=Validation.check_ip4
    )
    controller_user: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Controller user"
    )
    # TODO IMPROVE EOS-14361 mask secret
    controller_secret: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Controller password"
    )
    controller_type: str = ParamGroupInputBase._attr_ib(
        _param_group, descr=" Controller type"
    )


@attr.s(auto_attribs=True)
class StorageEnclosure(ParamGroupInputBase):
    controller_a_ip: str = StorageEnclosureParams.primary_ip
    controller_b_ip: str = StorageEnclosureParams.secondary_ip
    controller_user: str = StorageEnclosureParams.controller_user
    controller_secret: str = StorageEnclosureParams.controller_secret


class NodeNetworkParams():
    _param_group = 'node'
    hostname: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node hostname"
    )
    roles: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="List of roles assigned to the node"
    )
    data_public_interfaces: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="node data public network interfaces"
    )
    data_private_interfaces: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="node data private network interfaces"
    )
    bmc_user: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node BMC User"
    )
    # TODO IMPROVE EOS-14361 mask secret
    bmc_secret: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node BMC password"
    )
    mgmt_gateway: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node mgmt gateway IP",
        validator=Validation.check_ip4
    )
    mgmt_public_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node management interface IP",
        validator=Validation.check_ip4
    )
    mgmt_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node management interface netmask",
        validator=Validation.check_ip4
    )
    mgmt_interfaces: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="node management network interfaces"
    )
    data_public_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node data interface IP", default=UNCHANGED,
        validator=Validation.check_ip4
    )
    data_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node data interface netmask",
        validator=Validation.check_ip4
    )
    data_gateway: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node data gateway IP",
        validator=Validation.check_ip4
    )
    data_private_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node data interface private IP",
        validator=Validation.check_ip4
    )
    bmc_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="node BMC  IP", default=UNCHANGED,
        validator=Validation.check_ip4
    )


class NetworkParams():
    _param_group = 'network'
    cluster_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="cluster ip address for public data network",
        validator=Validation.check_ip4
    )
    mgmt_vip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="virtual ip address for management network",
        validator=Validation.check_ip4
    )
    dns_servers: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="list of dns servers as json"
    )
    search_domains: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="list of search domains as json"
    )
    primary_hostname: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node hostname"
    )
    primary_data_roaming_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node floating IP"
    )
    primary_data_gateway: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node data gateway IP"
    )
    primary_mgmt_gateway: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node mgmt gateway IP"
    )
    primary_mgmt_public_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node management interface IP"
    )
    primary_mgmt_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node management interface netmask"
    )
    primary_data_public_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node data interface IP",
        validator=Validation.check_ip4
    )
    primary_data_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node data interface netmask"
    )
    primary_data_network_iface: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node data network interface"
    )
    primary_bmc_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node BMC  IP",
        validator=Validation.check_ip4
    )
    primary_bmc_user: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node BMC User"
    )
    # TODO IMPROVE EOS-14361 mask secret
    primary_bmc_secret: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node BMC password"
    )
    secondary_hostname: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node hostname"
    )
    secondary_floating_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node floating IP"
    )
    secondary_data_gateway: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node data gateway IP"
    )
    secondary_mgmt_gateway: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node mgmt gateway IP"
    )
    secondary_mgmt_public_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node management interface IP",
        validator=Validation.check_ip4
    )
    secondary_mgmt_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node management interface netmask"
    )
    secondary_data_public_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node node data interface IP",
        validator=Validation.check_ip4
    )
    secondary_data_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node data interface netmask"
    )
    secondary_data_network_iface: List = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node data network interface"
    )
    secondary_bmc_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node BMC  IP",
        validator=Validation.check_ip4
    )
    secondary_bmc_user: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node BMC User"
    )
    # TODO IMPROVE EOS-14361 mask secret
    secondary_bmc_secret: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node BMC password"
    )


@attr.s(auto_attribs=True)
class Network(ParamGroupInputBase):
    cluster_ip: str = NetworkParams.cluster_ip
    mgmt_vip: str = NetworkParams.mgmt_vip
    dns_servers: List = NetworkParams.dns_servers
    search_domains: List = NetworkParams.search_domains
    primary_hostname: str = NetworkParams.primary_hostname
    primary_data_roaming_ip: str = NetworkParams.primary_data_roaming_ip
    primary_mgmt_public_ip: str = NetworkParams.primary_mgmt_public_ip
    primary_mgmt_netmask: str = NetworkParams.primary_mgmt_netmask
    primary_mgmt_gateway: str = NetworkParams.primary_mgmt_gateway
    primary_data_netmask: str = NetworkParams.primary_data_netmask
    primary_data_gateway: str = NetworkParams.primary_data_gateway
    primary_data_network_iface: List = NetworkParams.primary_data_network_iface
    primary_data_public_ip: str = NetworkParams.primary_data_public_ip
    primary_bmc_ip: str = NetworkParams.primary_bmc_ip
    primary_bmc_user: str = NetworkParams.primary_bmc_user
    primary_bmc_secret: str = NetworkParams.primary_bmc_secret
    secondary_hostname: str = NetworkParams.secondary_hostname
    secondary_floating_ip: str = NetworkParams.secondary_floating_ip
    secondary_mgmt_public_ip: str = NetworkParams.secondary_mgmt_public_ip
    secondary_mgmt_netmask: str = NetworkParams.secondary_mgmt_netmask
    secondary_data_gateway: str = NetworkParams.secondary_data_gateway
    secondary_mgmt_gateway: str = NetworkParams.secondary_mgmt_gateway
    secondary_data_netmask: str = NetworkParams.secondary_data_netmask
    secondary_data_network_iface: List = NetworkParams.secondary_data_network_iface  # noqa: E501
    secondary_bmc_ip: str = NetworkParams.secondary_bmc_ip
    secondary_bmc_user: str = NetworkParams.secondary_bmc_user
    secondary_bmc_secret: str = NetworkParams.secondary_bmc_secret
    secondary_data_public_ip: str = NetworkParams.secondary_data_public_ip


# # TODO TEST
# @attr.s(auto_attribs=True)
# class ClusterIP(ParamGroupInputBase):
#     _param_group = 'network'
#     # dns_server: str = ParamGroupInputBase._attr_ib(_param_group)
#     cluster_ip: str = ParamGroupInputBase._attr_ib(
#         _param_group, descr="cluster ip address for public data network",
#         default=attr.NOTHING
#     )


# # TODO TEST
# @attr.s(auto_attribs=True)
# class MgmtVIP(ParamGroupInputBase):
#     _param_group = 'network'
#     # dns_server: str = ParamGroupInputBase._attr_ib(_param_group)
#     mgmt_vip: str = ParamGroupInputBase._attr_ib(
#         _param_group, descr="virtual ip address for management network",
#         default=attr.NOTHING
#     )


# TODO
# verify that attributes match _param_di during class declaration:
#   - both attributes should satisfy _param_di
#   - is_key might be replaced with checking attr name against _param_di.key
class ParamDictItemInputBase(PrvsnrType, PillarItemsAPI):
    _param_di = None
    _param = None

    def pillar_items(self):  # TODO return type
        return iter({
            self.param_spec(): getattr(self, self._param_di.value)
        }.items())

    def param_spec(self):
        if self._param is None:
            key = getattr(self, self._param_di.key)
            self._param = Param(
                self._param_di.name / key,
                (self._param_di.keypath / key, self._param_di.fpath)
            )
        return self._param

    @classmethod
    def from_args(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fill_parser(cls, parser):
        ParserFiller.fill_parser(cls, parser, InputAttrParserArgs)

    @classmethod
    def extract_positional_args(cls, kwargs):
        return ParserFiller.extract_positional_args(cls, kwargs)

    @staticmethod
    def _attr_ib(
        is_key=False, default=UNCHANGED, descr='', metavar=None, **kwargs
    ):
        return attr.ib(
            default=attr.NOTHING if is_key else default,
            metadata={
                METADATA_ARGPARSER: {
                    'help': descr,
                    'metavar': metavar
                }
            },
            **kwargs
        )


@attr.s(auto_attribs=True)
class SWUpdateRepo(ParamDictItemInputBase):
    _param_di = param_spec['swupdate/repo']
    release: str = ParamDictItemInputBase._attr_ib(
        is_key=True,
        descr=("release version")
    )
    source: Union[str, Path] = ParamDictItemInputBase._attr_ib(
        descr=(
            "repo source, might be a local path to a repo folder or iso file"
            " or an url to a remote repo, "
            "{} might be used to remove the repo"
            .format(UNDEFINED)
        ),
        metavar='str',
        converter=lambda v: (
            UNCHANGED if v is None else (
                v if is_special(v) or isinstance(v, Path) else str(v)
            )
        )
    )
    _repo_params: Dict = attr.ib(init=False, default=attr.Factory(dict))
    _metadata: Dict = attr.ib(init=False, default=attr.Factory(dict))

    @source.validator
    def _check_source(self, attribute, value):
        if is_special(value):
            return  # TODO does any special is expected here

        if (
            type(self.source) is str
            and value.startswith(('http://', 'https://'))
        ):
            return

        reason = None
        _value = Path(str(value))
        if _value.exists():
            if _value.is_file():
                if _value.suffix != '.iso':
                    reason = 'not an iso file'
            elif not _value.is_dir():
                reason = 'not a file or directory'
        else:
            reason = 'unexpected type of source'

        if reason:
            logger.error(
                "Invalid source {}: {}"
                .format(str(value), reason)
            )
            raise SWUpdateRepoSourceError(str(value), reason)

    def __attrs_post_init__(self):
        if (
            type(self.source) is str
            and not self.source.startswith(('http://', 'https://'))
        ):
            self.source = Path(self.source)

        if isinstance(self.source, Path):
            self.source = self.source.resolve()

    @property
    def pillar_key(self):
        return self.release

    @property
    def pillar_value(self):
        if self.is_special() or self.is_remote():
            return self.source
        else:
            source = 'iso' if self.source.is_file() else 'dir'
            if self._repo_params:
                return {
                    'source': source,
                    'params': self._repo_params
                }
            else:
                return source

    @property
    def repo_params(self):
        return self._repo_params

    @repo_params.setter
    def repo_params(self, params: Dict):
        self._repo_params = params

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata: Dict):
        self._metadata = metadata

    def is_special(self):
        return is_special(self.source)

    def is_local(self):
        return not self.is_special() and isinstance(self.source, Path)

    def is_remote(self):
        return not (self.is_special() or self.is_local())

    def is_dir(self):
        return self.is_local() and self.source.is_dir()

    def is_iso(self):
        return self.is_local() and self.source.is_file()


@attr.s(auto_attribs=True)
class SWUpgradeRepo(SWUpdateRepo):
    _param_di = param_spec['swupgrade/repo']
