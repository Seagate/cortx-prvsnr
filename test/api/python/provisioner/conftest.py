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

import pytest

from provisioner.vendor import attr

from provisioner import (
    ALL_MINIONS, param, pillar, inputs, log
)


@pytest.fixture(scope='session', autouse=True)
def unit():
    pass


@pytest.fixture
def pillar_dir(monkeypatch, tmpdir_function):
    pillar_dir = tmpdir_function / 'pillar'
    pillar_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        pillar, 'PRVSNR_USER_PILLAR_ALL_HOSTS_DIR', pillar_dir
    )
    return pillar_dir


@pytest.fixture
def pillar_host_dir_tmpl(monkeypatch, pillar_dir):
    res = str(pillar_dir / '{minion_id}')
    monkeypatch.setattr(
        pillar, 'PRVSNR_USER_PILLAR_HOST_DIR_TMPL', res
    )
    return res


@pytest.fixture
def test_pillar(monkeypatch):
    _pillar = {
        'some-node-id-1': {
            '1': {
                '2': {
                    '3': '4',
                    '5': '6'
                },
                'di_parent': {}
            }
        },
        'some-node-id-2': {
            '1': {
                '2': {
                    '3': '5',
                    '5': '7'
                },
                'di_parent': {
                    '8': '9'
                }
            }
        }

    }

    def pillar_get(*args, targets=ALL_MINIONS, **kwargs):
        if targets == ALL_MINIONS:
            return _pillar
        else:
            return {k: v for k, v in _pillar.items() if k == targets}

    monkeypatch.setattr(
        pillar, 'pillar_get', pillar_get
    )

    return _pillar


@pytest.fixture
def param_spec(monkeypatch, pillar_dir, test_pillar):

    param1 = param.Param('some_param_gr/attr1', ('1/2/3', 'aaa.sls'))
    param2 = param.Param('some_param_gr/attr2', ('1/2/5', 'bbb.sls'))
    param3 = param.ParamDictItem(
        'some_param_gr2/attr1', ('1/di_parent', 'ccc.sls'),
        key='key_attr', value='value_attr'
    )

    param_spec = {
        str(param1.name): param1,
        str(param2.name): param2,
        str(param3.name): param3,
    }

    monkeypatch.setattr(
        inputs, 'param_spec', param_spec
    )

    return param_spec


@pytest.fixture
def some_param_gr(monkeypatch, param_spec):

    @attr.s(auto_attribs=True)
    class SomeParamGroup(inputs.ParamGroupInputBase):
        _param_group = 'some_param_gr'
        attr1: str = inputs.ParamGroupInputBase._attr_ib(_param_group)
        attr2: str = inputs.ParamGroupInputBase._attr_ib(_param_group)

    monkeypatch.setattr(
        inputs, 'SomeParamGroup', SomeParamGroup, raising=False
    )

    return SomeParamGroup


@pytest.fixture
def some_param_di(monkeypatch, param_spec):

    @attr.s(auto_attribs=True)
    class SomeParamDictItem(inputs.ParamDictItemInputBase):
        _param_di = param_spec['some_param_gr2/attr1']
        key_attr: str = inputs.ParamDictItemInputBase._attr_ib(is_key=True)
        value_attr: str = inputs.ParamDictItemInputBase._attr_ib()

    monkeypatch.setattr(
        inputs, 'SomeParamDictItem', SomeParamDictItem, raising=False
    )

    return SomeParamDictItem


@pytest.fixture
def mock_manager(mocker):
    return mocker.MagicMock()


@pytest.fixture
def log_args_builder(mocker, request):
    def _f(log_config):
        return log.build_log_args_cls(log_config)
    return _f
