import attr
import logging

from typing import List, Union, Any
from pathlib import Path

from .errors import UnknownParamError, EOSUpdateRepoSourceError
from .param import Param, ParamDictItem, KeyPath
from .api_spec import param_spec
from .values import (
    UNDEFINED, UNCHANGED, value_from_str,
    is_special
)
from .serialize import PrvsnrType

METADATA_PARAM_GROUP_KEY = '_param_group_key'
METADATA_ARGPARSER = '_param_argparser'

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class NoParams:
    @classmethod
    def fill_parser(cls, parser):
        pass

    @classmethod
    def extract_positional_args(cls, kwargs):
        return (), kwargs


@attr.s(auto_attribs=True)
class AttrParserArgs:
    attr: Any  # TODO typing

    name: str = attr.ib(init=False, default=None)
    action: str = attr.ib(init=False, default='store')
    metavar: str = attr.ib(init=False, default=None)
    default: str = attr.ib(init=False, default=None)
    help: str = attr.ib(init=False, default='')
    type: Any = attr.ib(init=False, default=None)  # TODO typing

    def __attrs_post_init__(self):
        self.name = self.attr.name

        parser_args = self.attr.metadata.get(
            METADATA_ARGPARSER, {}
        )

        if self.attr.type is bool:
            self.action = 'store_true'

        self.type = value_from_str

        self.help = parser_args.get('help', self.help)

        if self.attr.default is not attr.NOTHING:
            # optional argument
            self.name = '--' + self.name.replace('_', '-')
            self.default = self.attr.default
            self.metavar = (
                parser_args.get('metavar')
                or (self.attr.type.__name__ if self.attr.type else None)
            )
            if self.metavar:
                self.metavar = self.metavar.upper()

    @property
    def kwargs(self):
        def _filter(attr, value):
            not_filter = ['attr', 'name']
            if self.action == 'store_true':
                not_filter.extend(['metavar', 'type', 'default'])
            return attr.name not in not_filter

        return attr.asdict(self, filter=_filter)


# TODO test
class ParserFiller:
    @staticmethod
    def fill_parser(cls, parser):
        for _attr in attr.fields(cls):
            if METADATA_ARGPARSER in _attr.metadata:
                args = AttrParserArgs(_attr)
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
                        param_di.pi_path,
                        param_di.pi_key / key_path.leaf
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


class ParamGroupInputBase:
    _param_group = None
    _spec = None

    def __iter__(self):  # TODO return type
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
        ParserFiller.fill_parser(cls, parser)

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


@attr.s(auto_attribs=True)
class Network(ParamGroupInputBase):
    _param_group = 'network'
    # dns_server: str = ParamGroupInputBase._attr_ib(_param_group)
    cluster_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="cluster ip address for public data network"
    )
    mgmt_vip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="virtual ip address for management network"
    )
    dns_servers: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="list of dns servers"
    )
    search_domains: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="list of search domains"
    )
    primary_hostname: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node hostname"
    )
    primary_floating_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node floating IP"
    )
    primary_gateway_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node gateway IP"
    )
    primary_mgmt_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node management iface IP"
    )
    primary_mgmt_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node management iface netmask"
    )
    primary_data_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node data iface IP"
    )
    primary_data_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="primary node data iface netmask"
    )
    secondary_hostname: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node hostname"
    )
    secondary_floating_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node floating IP"
    )
    secondary_gateway_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node gateway IP"
    )
    secondary_mgmt_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node management iface IP"
    )
    secondary_mgmt_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node management iface netmask"
    )
    secondary_data_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node node data iface IP"
    )
    secondary_data_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="secondary node data iface netmask"
    )


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
class ParamDictItemInputBase(PrvsnrType):
    _param_di = None
    _param = None

    def __iter__(self):  # TODO return type
        return iter({
            self.param_spec(): getattr(self, self._param_di.value)
        }.items())

    def param_spec(self):
        if self._param is None:
            key = getattr(self, self._param_di.key)
            self._param = Param(
                self._param_di.name / key,
                self._param_di.pi_path,
                self._param_di.pi_key / key
            )
        return self._param

    @classmethod
    def from_args(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fill_parser(cls, parser):
        ParserFiller.fill_parser(cls, parser)

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
class EOSUpdateRepo(ParamDictItemInputBase):
    _param_di = param_spec['eosupdate/repo']
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
            raise EOSUpdateRepoSourceError(str(value), reason)

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
            return 'iso' if self.source.is_file() else 'dir'

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
