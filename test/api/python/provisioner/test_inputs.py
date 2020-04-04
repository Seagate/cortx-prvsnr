import pytest
import attr
from typing import Any, Union
from pathlib import Path

from provisioner.errors import EOSUpdateRepoSourceError
from provisioner import values
from provisioner.values import UNCHANGED
from provisioner import inputs
from provisioner.param import (
    Param, ParamDictItem
)
from provisioner.inputs import (
    METADATA_PARAM_GROUP_KEY,
    METADATA_ARGPARSER,
    AttrParserArgs,
    ParamsList,
    ParamGroupInputBase,
    NTP, Network,
    ParamDictItemInputBase,
    EOSUpdateRepo
)


test_param_spec = {
    'some_param_gr/attr1': Param(
        'some_param_gr/attr1', 'some-pi-path1', 'some-pi-key1'
    ),
    'some_param_gr/attr2': Param(
        'some_param_gr/attr2', 'some-pi-path2', 'some-pi-key2'
    ),
    'some/dict/item1': ParamDictItem(
        'some/dict/item1', 'some-pi-path3', 'some-pi-key3',
        'some_key_attr', 'some_value_attr'
    )
}


@attr.s(auto_attribs=True)
class SomeParamGroup(ParamGroupInputBase):
    _param_group = 'some_param_gr'
    attr1: Any = ParamGroupInputBase._attr_ib(_param_group)
    attr2: int = ParamGroupInputBase._attr_ib(_param_group, default=1)


@attr.s(auto_attribs=True)
class SomeParamDictItem(ParamDictItemInputBase):
    _param_di = test_param_spec['some/dict/item1']
    some_key_attr: str = ParamDictItemInputBase._attr_ib(
        is_key=True, descr='some_key_attr descr'
    )
    some_value_attr: str = ParamDictItemInputBase._attr_ib(
        descr='some_value_attr descr'
    )


@pytest.fixture(scope="module")
def param_spec():
    return test_param_spec


@pytest.fixture
def param_spec_mocked(monkeypatch, param_spec):
    monkeypatch.setattr(
        inputs, 'param_spec', param_spec
    )
    return param_spec


# AttrParserArgs tests
def test_attr_parser_args_kwargs_keys_by_default():
    SC = attr.make_class("SC", {"x": attr.ib(type=str, default='123')})
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'metavar', 'default', 'help', 'type'))


def test_attr_parser_args_kwargs_keys_for_boolean():
    SC = attr.make_class("SC", {"x": attr.ib(type=bool, default=False)})
    assert set(
        AttrParserArgs(attr.fields(SC).x).kwargs.keys()
    ) == set(('action', 'help'))


def test_attr_parser_args_name_for_optional():
    SC = attr.make_class("SC", {"x": attr.ib(default=None)})
    assert AttrParserArgs(attr.fields(SC).x).name == '--x'


def test_attr_parser_args_name_for_optional_with_underscore():
    SC = attr.make_class("SC", {"x_y": attr.ib(default=None)})
    assert AttrParserArgs(attr.fields(SC).x_y).name == '--x-y'


def test_attr_parser_args_name_for_positional():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).name == 'x'


def test_attr_parser_args_action_by_default():
    SC = attr.make_class("SC", {"x": attr.ib(default=None)})
    assert AttrParserArgs(attr.fields(SC).x).action == 'store'


def test_attr_parser_args_action_for_boolean():
    SC = attr.make_class("SC", {"x": attr.ib(default=None, type=bool)})
    assert AttrParserArgs(attr.fields(SC).x).action == 'store_true'


def test_attr_parser_args_default_set():
    SC = attr.make_class("SC", {"x": attr.ib(default=123)})
    assert AttrParserArgs(attr.fields(SC).x).name == '--x'
    assert AttrParserArgs(attr.fields(SC).x).default == 123


def test_attr_parser_args_default_not_set():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).name == 'x'
    assert AttrParserArgs(attr.fields(SC).x).default is None


def test_attr_parser_args_type():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).type == values.value_from_str


def test_attr_parser_args_no_metavar_for_positional():
    SC = attr.make_class("SC", {"x": attr.ib()})
    assert AttrParserArgs(attr.fields(SC).x).metavar is None


def test_attr_parser_args_metavar_by_default_for_optional():
    SC = attr.make_class("SC", {"x": attr.ib(type=str, default='123')})
    assert AttrParserArgs(attr.fields(SC).x).metavar == 'STR'


def test_attr_parser_args_metavar_from_metadata_for_optional():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'metavar': 'SOME-METAVAR'
                },
            },
            default='123'
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).metavar == 'SOME-METAVAR'


def test_attr_parser_args_help_by_default_for_optional():
    SC = attr.make_class("SC", {"x": attr.ib(type=str, default='123')})
    assert AttrParserArgs(attr.fields(SC).x).help == ''


def test_attr_parser_args_help_from_metadata_for_optional():
    SC = attr.make_class("SC", {
        "x": attr.ib(
            type=str,
            metadata={
                METADATA_ARGPARSER: {
                    'help': 'some help'
                },
            }
        )
    })
    assert AttrParserArgs(attr.fields(SC).x).help == 'some help'


# ParamsList tests
def test_params_list_from_args(param_spec_mocked):
    params = [
        param_spec_mocked['some_param_gr/attr2'],
        Param(
            param_spec_mocked['some/dict/item1'].name / 'key1',
            'some-pi-path3',
            'some-pi-key3/key1'
        )
    ]
    assert ParamsList.from_args(*[str(p) for p in params]).params == params
    assert ParamsList.from_args(*[p for p in params]).params == params
    assert ParamsList.from_args(
        *[str(p) for p in params],
        *[p for p in params]
    ).params == params + params


def test_params_list_iter(param_spec_mocked):
    params = ParamsList.from_args(
        'some_param_gr/attr1', 'some/dict/item1/some-key'
    )
    assert [p for p in params] == params.params


def test_param_group_input_base_attr_ib():
    attr1 = attr.fields(SomeParamGroup).attr1
    assert attr1.type is Any
    assert attr1.default is UNCHANGED
    assert attr1.metadata[METADATA_PARAM_GROUP_KEY] == 'some_param_gr'

    attr2 = attr.fields(SomeParamGroup).attr2
    assert attr2.type is int
    assert attr2.default == 1
    assert attr2.metadata[METADATA_PARAM_GROUP_KEY] == 'some_param_gr'


def test_param_group_input_base_from_args():
    test = SomeParamGroup.from_args(attr1='1234', attr2=5)
    assert test.attr1 == '1234'
    assert test.attr2 == 5


def test_param_group_input_base_param_spec(param_spec_mocked):
    SomeParamGroup.param_spec('attr1') is param_spec_mocked[
        'some_param_gr/attr1'
    ]
    SomeParamGroup.param_spec('attr2') is param_spec_mocked[
        'some_param_gr/attr2'
    ]


def test_param_group_input_base_iter(param_spec_mocked):
    test = SomeParamGroup('123', 45)
    for param, value in test:
        assert param is param_spec_mocked[str(param.name)]
        assert value == getattr(test, param.name.leaf)


def test_ntp():
    assert NTP._param_group == 'ntp'
    for f in ('server', 'timezone'):
        fattr = attr.fields_dict(NTP)[f]
        assert fattr.type is str
        assert fattr.default is UNCHANGED


def test_network():
    assert Network._param_group == 'network'
    for f in (
        'primary_mgmt_ip',
        'primary_data_ip',
        'primary_gateway_ip',
        'primary_hostname',
        'secondary_mgmt_ip',
        'secondary_data_ip',
        'secondary_gateway_ip',
        'secondary_hostname'
     ):
        fattr = attr.fields_dict(Network)[f]
        assert fattr.type is str
        assert fattr.default is UNCHANGED


def test_param_dict_item_input_base_attr_ib():
    some_key_attr = attr.fields(SomeParamDictItem).some_key_attr
    assert some_key_attr.type is str
    assert some_key_attr.default is attr.NOTHING
    assert some_key_attr.metadata[METADATA_ARGPARSER]['help'] == (
        'some_key_attr descr'
    )

    some_value_attr = attr.fields(SomeParamDictItem).some_value_attr
    assert some_value_attr.type is str
    assert some_value_attr.default == UNCHANGED
    assert some_value_attr.metadata[METADATA_ARGPARSER]['help'] == (
        'some_value_attr descr'
    )


def test_param_dict_item_input_base_from_args():
    test = SomeParamDictItem.from_args(some_key_attr='1234', some_value_attr=5)
    assert test.some_key_attr == '1234'
    assert test.some_value_attr == 5


def test_param_dict_item_input_base_param_spec(param_spec_mocked):
    test = SomeParamDictItem(some_key_attr='1234', some_value_attr=5)
    assert test.param_spec() == Param(
        'some/dict/item1/1234', 'some-pi-path3', 'some-pi-key3/1234'
    )


def test_param_dict_item_input_base_iter(param_spec_mocked):
    test = SomeParamDictItem('123', 45)
    _iter = iter(test)
    param, value = next(_iter)
    assert param == test.param_spec()
    assert value == 45
    # only one item
    with pytest.raises(StopIteration):
        next(_iter)


def test_eos_update_repo_attrs():
    assert EOSUpdateRepo._param_di == inputs.param_spec['eosupdate/repo']

    fattr = attr.fields_dict(EOSUpdateRepo)['release']
    assert fattr.type is str
    assert fattr.default is attr.NOTHING

    fattr = attr.fields_dict(EOSUpdateRepo)['source']
    assert fattr.type is Union[str, Path]
    assert fattr.default is UNCHANGED


@pytest.mark.patch_logging([(inputs, ('error',))])
def test_eos_update_repo_source_init(tmpdir_function, patch_logging):
    some_release = '1.2.3'

    # special values
    for source in values._values.values():
        res = EOSUpdateRepo(some_release, source=source)
        assert res.source == source

    res = EOSUpdateRepo(some_release, source=None)
    assert res.source == UNCHANGED

    # directory
    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()
    for source in (repo_dir, str(repo_dir)):
        res = EOSUpdateRepo(some_release, source=source)
        assert res.source == repo_dir

    # iso file
    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()
    for source in (repo_iso, str(repo_iso)):
        res = EOSUpdateRepo(some_release, source=source)
        assert res.source == repo_iso

    # other existent file object
    non_iso_file = tmpdir_function / 'repo.file'
    non_iso_file.touch()
    with pytest.raises(EOSUpdateRepoSourceError) as excinfo:
        EOSUpdateRepo(some_release, source=str(non_iso_file))
    assert excinfo.value.source == str(non_iso_file)
    assert excinfo.value.reason == 'not an iso file'

    # existent object but neither file nor dir
    bad_object = '/dev/null'
    with pytest.raises(EOSUpdateRepoSourceError) as excinfo:
        EOSUpdateRepo(some_release, source=bad_object)
    assert excinfo.value.source == bad_object
    assert excinfo.value.reason == 'not a file or directory'

    # urls are expected to start with http:// or https://
    for source in ('http://some/http/url', 'https://some/http/url'):
        res = EOSUpdateRepo(some_release, source=source)
        assert res.source == source

    # any other cases are treated as invalid
    source = 'some/string'
    with pytest.raises(EOSUpdateRepoSourceError) as excinfo:
        res = EOSUpdateRepo(some_release, source=source)
    assert excinfo.value.source == source
    assert excinfo.value.reason == 'unexpected type of source'

    # TODO non absolute existent one

    # non canonical absolute path
    res = EOSUpdateRepo(some_release, source=(repo_dir / '..' / 'repo.iso'))
    assert res.source == repo_iso


def test_eos_update_repo_pillar_key(tmpdir_function):
    some_release = '1.2.3'

    res = EOSUpdateRepo(some_release, source='http://some/http/url')
    assert res.pillar_key == some_release


def test_eos_update_repo_pillar_value(tmpdir_function):
    some_release = '1.2.3'

    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()

    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()

    # special values
    for source in values._values.values():
        res = EOSUpdateRepo(some_release, source=source)
        assert res.pillar_value == source

    res = EOSUpdateRepo(some_release, source=None)
    assert res.pillar_value == UNCHANGED

    # directory
    res = EOSUpdateRepo(some_release, source=repo_dir)
    assert res.pillar_value == 'dir'

    # iso file
    res = EOSUpdateRepo(some_release, source=repo_iso)
    assert res.pillar_value == 'iso'

    # urls are expected to start with http:// or https://
    for source in ('http://some/http/url', 'https://some/http/url'):
        res = EOSUpdateRepo(some_release, source=source)
        assert res.pillar_value == source


def test_eos_update_repo_is_apis(tmpdir_function):
    some_release = '1.2.3'

    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()

    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()

    res = None

    def _check(*args):
        for api in ('is_special', 'is_local', 'is_remote', 'is_dir', 'is_iso'):
            assert getattr(res, api)() == (api in args)

    # special values
    for source in values._values.values():
        res = EOSUpdateRepo(some_release, source=source)
        _check('is_special')

    res = EOSUpdateRepo(some_release, source=None)
    _check('is_special')

    # directory
    res = EOSUpdateRepo(some_release, source=repo_dir)
    _check('is_local', 'is_dir')

    # iso file
    res = EOSUpdateRepo(some_release, source=repo_iso)
    _check('is_local', 'is_iso')

    # urls
    res = EOSUpdateRepo(some_release, source='https://some/http/url')
    _check('is_remote')
