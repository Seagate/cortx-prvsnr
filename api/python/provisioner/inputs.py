import attr
from typing import List, Union
from pathlib import Path

from .errors import UnknownParamError
from .param import Param, ParamDictItem, KeyPath
from .api_spec import param_spec
from .values import (
    UNDEFINED, UNCHANGED, value_from_str,
    is_special
)

METADATA_PARAM_GROUP_KEY = '_param_group_key'
METADATA_PARAM_DESCR = '_param_description'


@attr.s(auto_attribs=True)
class NoParams:
    @classmethod
    def fill_parser(cls, parser):
        pass


# TODO test
class ParserFiller:
    def fill_parser(cls, parser):
        for _attr in attr.fields(cls):
            name = _attr.name
            kwargs = dict(
                metavar=_attr.type.__name__.upper(),
                type=value_from_str,
                help=_attr.metadata.get(METADATA_PARAM_DESCR, '')
            )
            if _attr.default is not attr.NOTHING:
                name = '--' + _attr.name
                kwargs['default'] = _attr.default
            else:
                kwargs['metavar'] = None
            parser.add_argument(name, **kwargs)


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
                    raise UnknownParamError(str(key_path))
            params.append(param)
        return cls(params)

    @classmethod
    def fill_parser(cls, parser):
        parser.add_argument(
            'args', metavar='param', type=str, nargs='+',
            help='a param name to get'
        )


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
                raise ValueError('unknown attr {}'.format(attr_name))
            else:
                full_path = "{}/{}".format(
                    _attr.metadata.get(METADATA_PARAM_GROUP_KEY, ''), attr_name
                )
                cls._spec[attr_name] = param_spec[full_path]
        return cls._spec[attr_name]

    @classmethod
    def from_args(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fill_parser(cls, parser):
        ParserFiller.fill_parser(cls, parser)

    @staticmethod
    def _attr_ib(param_group='', default=UNCHANGED, descr='', **kwargs):
        return attr.ib(
            default=default,
            metadata={
                METADATA_PARAM_GROUP_KEY: param_group,
                METADATA_PARAM_DESCR: descr
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
    slave_hostname: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node hostname"
    )
    slave_floating_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node floating IP"
    )
    slave_gateway_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node gateway IP"
    )
    slave_mgmt_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node management iface IP"
    )
    slave_mgmt_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node management iface netmask"
    )
    slave_data_ip: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node node data iface IP"
    )
    slave_data_netmask: str = ParamGroupInputBase._attr_ib(
        _param_group, descr="slave node data iface netmask"
    )


# TODO
# verify that attributes match _param_di during class declaration:
#   - both attributes should satisfy _param_di
#   - is_key might be replaced with checking attr name against _param_di.key
class ParamDictItemInputBase:
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

    @staticmethod
    def _attr_ib(is_key=False, default=UNCHANGED, descr='', **kwargs):
        return attr.ib(
            default=attr.NOTHING if is_key else default,
            metadata={
                METADATA_PARAM_DESCR: descr
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
    source: str = ParamDictItemInputBase._attr_ib(
        descr=(
            "repo source, might be a local path to a repo folder or iso file"
            " or an url to a remote repo, "
            "{} might be used to remove the repo"
            .format(UNDEFINED)
        )
    )

    @source.validator
    def _check_source(self, attribute, value):
        if value is not None:
            if is_special(value):
                return
            if type(value) is not str:
                raise TypeError(
                    'unexpected type {} of value {}'
                    .format(type(value), value)
                )
            value = Path(value)
            if value.exists():
                if value.is_dir() or (
                    value.is_file() and (value.suffix == '.iso')
                ):
                    return
            else:  # treate as url TODO check url is valid or even is reachable
                return
            raise ValueError('value {} is not acceptable'.format(value))

    def __attrs_post_init__(self):
        if type(self.source) is str:
            if Path(self.source).is_dir():
                self.source = "file://{}".format(self.source)
