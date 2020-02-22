import pytest
from pathlib import Path

from provisioner.param import (
    KeyPath, Param, ParamDictItem
)

# TODO tests for validators and converters


def test_key_path_to_str():
    path = '1/2/3/4/5'
    assert str(KeyPath(path)) == str(Path(path))


def test_key_path_truediv():
    path = '1/2/3/4/5'
    assert KeyPath(path) / '6' == KeyPath(Path(path) / '6')


def test_key_path_parent_dict():
    key_dict = {'1': {'2': '3'}}
    assert KeyPath('1/2').parent_dict(key_dict) is key_dict['1']

    with pytest.raises(KeyError):
        KeyPath('1/4/5').parent_dict(key_dict, fix_missing=False)

    assert KeyPath('1/4/5').parent_dict(key_dict) is key_dict['1']['4']


def test_key_path_parent():
    assert KeyPath('1/2/3/4').parent == KeyPath('1/2/3')


def test_key_path_leaf():
    assert KeyPath('1/2').leaf == '2'


def test_key_path_value():
    key_dict = {'1': {'2': '3'}}
    assert KeyPath('1/2').value(key_dict) == '3'

    with pytest.raises(KeyError):
        KeyPath('1/3').value(key_dict)


def test_key_path_is_hashable():
    hash(KeyPath('1/2/3'))


def test_param_is_hashable():
    hash(Param('1', '2', '3'))


def test_param_dict_item_is_hashable():
    hash(ParamDictItem('1', '2', '3', '4', '5'))


def test_param_dict_item_from_spec():
    pdi = ParamDictItem('1', '2', '3', '4', '5')
    assert ParamDictItem.from_spec(
        name=str(pdi.name),
        parent=str(pdi.pi_key),
        _path=str(pdi.pi_path),
        key=str(pdi.key),
        value=str(pdi.value),
    ) == pdi
