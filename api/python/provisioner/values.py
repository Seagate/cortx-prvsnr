from .config import PRVSNR_VALUES_PREFIX

_values = {}


class _Singletone:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            _values[str(cls._instance)] = cls._instance
        return cls._instance

    def __repr__(self):
        return PRVSNR_VALUES_PREFIX + type(self).__name__.upper()[1:]


class _Unchanged(_Singletone):
    pass


class _Default(_Singletone):
    pass


class _Undefined(_Singletone):
    pass


class _Missed(_Singletone):
    pass


UNCHANGED = _Unchanged()
DEFAULT = _Default()
UNDEFINED = _Undefined()
MISSED = _Missed()


def value_from_str(value: str):
    return _values.get(value, value)


def is_special(value):
    return value and (_values.get(str(value)) is value)
