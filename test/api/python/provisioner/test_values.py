from provisioner.config import PRVSNR_VALUES_PREFIX
from provisioner import values


def test_singletone():
    try:
        class Abcde(values._Singletone):
            pass

        abcde = Abcde()
        cls_str = PRVSNR_VALUES_PREFIX + 'BCDE'
        assert Abcde() is abcde
        assert str(abcde) == repr(abcde) == cls_str
        assert values._values[cls_str] is abcde
    finally:
        values._values.pop(cls_str, None)


def test_is_special():
    for value in values._values.values():
        assert values.is_special(value)
        assert not values.is_special(str(value))
    assert not values.is_special(None)


def test_value_from_str():
    for value in values._values:
        values.value_from_str(value) is getattr(
            values, value.replace(PRVSNR_VALUES_PREFIX, '')
        )
    value = 'other'
    assert values.value_from_str(value) is value
