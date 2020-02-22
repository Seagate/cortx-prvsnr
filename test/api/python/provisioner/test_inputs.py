import pytest
import attr
from typing import Any

from provisioner.values import UNCHANGED
from provisioner import inputs
from provisioner.param import (
    Param, ParamDictItem
)
from provisioner.inputs import (
    METADATA_PARAM_GROUP_KEY, METADATA_PARAM_DESCR,
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
        'slave_mgmt_ip',
        'slave_data_ip',
        'slave_gateway_ip',
        'slave_hostname'
     ):
        fattr = attr.fields_dict(Network)[f]
        assert fattr.type is str
        assert fattr.default is UNCHANGED


def test_param_dict_item_input_base_attr_ib():
    some_key_attr = attr.fields(SomeParamDictItem).some_key_attr
    assert some_key_attr.type is str
    assert some_key_attr.default is attr.NOTHING
    assert some_key_attr.metadata[METADATA_PARAM_DESCR] == (
        'some_key_attr descr'
    )

    some_value_attr = attr.fields(SomeParamDictItem).some_value_attr
    assert some_value_attr.type is str
    assert some_value_attr.default == UNCHANGED
    assert some_value_attr.metadata[METADATA_PARAM_DESCR] == (
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
    assert fattr.type is str
    assert fattr.default is UNCHANGED


def test_eos_update_repo_source_validator(tmpdir_function):
    some_release = '1.2.3'

    res = EOSUpdateRepo(some_release, source=UNCHANGED)

    repo_dir = tmpdir_function / 'repo'
    repo_dir.mkdir()
    res = EOSUpdateRepo(some_release, source=str(repo_dir))
    assert res.source == "file://{}".format(repo_dir)

    repo_iso = tmpdir_function / 'repo.iso'
    repo_iso.touch()
    EOSUpdateRepo(some_release, source=str(repo_iso))

    non_iso_file = tmpdir_function / 'repo.file'
    non_iso_file.touch()
    with pytest.raises(ValueError):
        EOSUpdateRepo(some_release, source=str(non_iso_file))

    # any other case is treated as url
    EOSUpdateRepo(some_release, source='any/other/case/treated/as/url')
