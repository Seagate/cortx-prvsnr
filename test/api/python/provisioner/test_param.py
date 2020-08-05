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
