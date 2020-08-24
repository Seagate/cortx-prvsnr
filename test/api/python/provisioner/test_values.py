#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
# please email opensource@seagate.com or cortx-questions@seagate.com."
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
