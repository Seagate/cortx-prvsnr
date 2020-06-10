from pathlib import Path

from provisioner.pillar import (
    KeyPath, PillarKeyAPI, PillarKey
)
from provisioner.param import (
    Param, ParamDictItem
)


# TODO tests for validators and converters


def test_param_Param_mro():
    assert issubclass(Param, PillarKeyAPI)


def test_param_Param_init():
    name = '1/2/3'
    kp = '6/7/8'
    fp = 'q/w/e'

    for _kp in (kp, Path(kp), KeyPath(kp)):
        assert Param(name, _kp) == Param(name, PillarKey(kp))
    assert Param(name, (kp, fp)) == Param(name, PillarKey(kp, fp))


def test_param_Param_to_str():
    name = '1/2/3'
    kp = '6/7/8'
    assert str(Param(name, kp)) == name


def test_param_Param_is_hashable():
    hash(Param('1', ('2', '3')))


def test_param_ParamDictItem_is_hashable():
    hash(ParamDictItem('1', ('2', '3'), '4', '5'))


def test_param_ParamDictItem_from_spec():
    pdi = ParamDictItem('1', ('2', '3'), '4', '5')
    assert ParamDictItem.from_spec(
        name=str(pdi.name),
        parent=str(pdi.keypath),
        _path=str(pdi.fpath),
        key=str(pdi.key),
        value=str(pdi.value),
    ) == pdi
