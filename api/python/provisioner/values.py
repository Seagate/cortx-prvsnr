from .config import PRVSNR_VALUES_PREFIX

_values = {}


class _Singletone:
    _prvsnr_type_ = True
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


class _PrvsnrValue(_Singletone):
    def __new__(cls):
        instance = super().__new__(cls)
        if str(instance) not in _values:
            _values[str(instance)] = instance
        return instance

    def __repr__(self):
        return PRVSNR_VALUES_PREFIX + type(self).__name__.upper()[1:]


class _Unchanged(_PrvsnrValue):
    pass


class _Default(_PrvsnrValue):
    pass


class _Undefined(_PrvsnrValue):
    pass


class _Missed(_PrvsnrValue):
    pass


class _None(_PrvsnrValue):
    pass


UNCHANGED = _Unchanged()
DEFAULT = _Default()
UNDEFINED = _Undefined()
MISSED = _Missed()
NONE = _None()


def value_from_str(value: str):
    return _values.get(value, value)


def is_special(value):
    return value and (_values.get(str(value)) is value)
