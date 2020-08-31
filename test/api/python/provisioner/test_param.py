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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

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
