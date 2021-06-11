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

from .config import PRVSNR_VALUES_PREFIX

_values = {}


# FIXME very poor implementation, need to review
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
