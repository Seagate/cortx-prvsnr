#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

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
