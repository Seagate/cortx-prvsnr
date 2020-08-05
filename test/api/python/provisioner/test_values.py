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

from provisioner.config import PRVSNR_VALUES_PREFIX
from provisioner import values


def test_singletone():
    class Abcde(values._Singletone):
        pass

    abcde = Abcde()
    assert Abcde() is abcde


def test_prvsnr_value():
    try:
        class Abcde(values._PrvsnrValue):
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
