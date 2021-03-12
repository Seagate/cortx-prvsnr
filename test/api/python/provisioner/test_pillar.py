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

import pytest
from copy import deepcopy
from pathlib import Path

from provisioner.utils import dump_yaml, load_yaml
from provisioner.param import Param
from provisioner import (
    pillar, ALL_MINIONS, UNCHANGED, DEFAULT, MISSED, UNDEFINED
)
from provisioner.pillar import (
    KeyPath, PillarKeyAPI, PillarKey,
    PillarEntry, PillarResolver, PillarUpdater
)

from .helper import mock_fun_echo

add_pillar_merge_prefix = PillarUpdater.add_merge_prefix

# TODO tests for validators and converters

# ### KeyPath ###


def test_pillar_KeyPath_init():
    with pytest.raises(TypeError):
        KeyPath(None)


def test_pillar_KeyPath_to_str():
    path = '1/2/3/4/5'
    assert str(KeyPath(path)) == str(Path(path))


def test_pillar_KeyPath_truediv():
    path = '1/2/3/4/5'
    assert KeyPath(path) / '6' == KeyPath(Path(path) / '6')


def test_pillar_KeyPath_parent_dict():
    key_dict = {'1': {'2': '3'}}
    assert KeyPath('1/2').parent_dict(key_dict) is key_dict['1']

    with pytest.raises(KeyError):
        KeyPath('1/4/5').parent_dict(key_dict, fix_missing=False)

    assert KeyPath('1/4/5').parent_dict(key_dict) is key_dict['1']['4']


def test_pillar_KeyPath_parent():
    assert KeyPath('1/2/3/4').parent == KeyPath('1/2/3')


def test_pillar_KeyPath_leaf():
    assert KeyPath('1/2').leaf == '2'


def test_pillar_KeyPath_value():
    key_dict = {'1': {'2': '3'}}
    assert KeyPath('1/2').value(key_dict) == '3'

    with pytest.raises(KeyError):
        KeyPath('1/3').value(key_dict)


def test_pillar_KeyPath_is_hashable():
    hash(KeyPath('1/2/3'))


# ### PillarKey ###

def test_pillar_PillarKey_mro():
    assert issubclass(PillarKey, PillarKeyAPI)


def test_pillar_PillarKey_init():
    keypath = '1/2/3/4/5'
    assert PillarKey(keypath) == PillarKey(keypath, '1.sls')
    assert PillarKey(keypath, 'some.sls').fpath == Path('some.sls')
    assert PillarKey(keypath, Path('some.sls')).fpath == Path('some.sls')
    assert PillarKey(keypath) == PillarKey(KeyPath(keypath))
    # short keypath
    assert PillarKey('1') == PillarKey('1', '1.sls')
    # incorrect keypaths
    with pytest.raises(TypeError):
        PillarKey(None)
    for kp in ('', '.', '/'):
        with pytest.raises(ValueError):
            PillarKey(kp)


def test_pillar_PillarKey_to_str():
    keypath = '1/2/3/4/5'
    assert str(PillarKey(keypath)) == keypath


# TODO TEST
@pytest.mark.skip(reason='not implemented')
def test_pillar_PillarKeysList_fill_parser():
    raise NotImplementedError


# TODO TEST
@pytest.mark.skip(reason='not implemented')
def test_pillar_PillarKeysList_extract_positional_args():
    raise NotImplementedError


# ### PillarEntry ###

def test_pillar_PillarEntry_get():
    pillar = {'1': {'2': '3'}}

    assert PillarEntry('1/2', pillar).get() == '3'
    assert PillarEntry('1/4', pillar).get() == MISSED


def test_pillar_PillarEntry_set():
    pillar = {'1': {'2': '3'}}

    pe = PillarEntry('1/2', pillar)

    pe.set('4')
    assert pillar['1']['2'] == '4'
    assert pe.get() == '4'

    # nothing happens for the next time
    pe.set('5')
    assert pe.get() == '4'

    # new key
    pe = PillarEntry('1/5', pillar)
    pe.set('6')
    assert pillar['1']['5'] == '6'
    assert pe.get() == '6'

    # list value
    pe = PillarEntry('1/5', pillar)
    list_v = [1, 2, '3']
    pe.set(list_v)
    assert pillar['1']['5'] == list_v
    assert pe.get() == list_v


def test_pillar_PillarEntry_rollback():
    pillar = {'1': {'2': '3'}}

    pe = PillarEntry('1/2', pillar)
    pe.set('4')
    pe.rollback()
    assert pe.get() == '3'

    # nothing happens for the next time
    pe.set('4')
    assert pe.get() == '3'

    pillar = {'1': {'2': '3'}}

    # UNCHANGED
    pe = PillarEntry('1/2', pillar)
    pe.set(UNCHANGED)
    pe.rollback()
    assert pillar == {'1': {'2': '3'}}

    # DEFAULT (reset)
    pe = PillarEntry('1/2', pillar)
    pe.set(DEFAULT)
    pe.rollback()
    assert pillar == {'1': {'2': '3'}}


def test_pillar_resolver(test_pillar):
    param1 = Param('some-param', ('1/2/3', 'aaa.sls'))
    param2 = Param('some-param2', ('1/2/5', 'aaa.sls'))
    param3 = Param('some-param2', ('1/di_parent/8', 'aaa.sls'))

    _iter = iter(test_pillar)
    minion_id_1 = next(_iter)
    minion_id_2 = next(_iter)

    pr = PillarResolver()
    assert pr.pillar is test_pillar

    res = pr.get([param1])
    assert res == {
        minion_id_1: {
            param1: test_pillar[minion_id_1]['1']['2']['3']
        }, minion_id_2: {
            param1: test_pillar[minion_id_2]['1']['2']['3']
        }
    }

    res = pr.get([param2])
    assert res == {
        minion_id_1: {
            param2: test_pillar[minion_id_1]['1']['2']['5']
        }, minion_id_2: {
            param2: test_pillar[minion_id_2]['1']['2']['5']
        }
    }

    res = pr.get([param3])
    assert res == {
        minion_id_1: {
            param3: MISSED
        }, minion_id_2: {
            param3: test_pillar[minion_id_2]['1']['di_parent']['8']
        }
    }

    res = pr.get([param1, param2, param3])
    assert res == {
        minion_id_1: {
            param1: test_pillar[minion_id_1]['1']['2']['3'],
            param2: test_pillar[minion_id_1]['1']['2']['5'],
            param3: MISSED
        }, minion_id_2: {
            param1: test_pillar[minion_id_2]['1']['2']['3'],
            param2: test_pillar[minion_id_2]['1']['2']['5'],
            param3: test_pillar[minion_id_2]['1']['di_parent']['8']
        }
    }

    pr = PillarResolver(targets=minion_id_1)
    assert pr.pillar == {
        k: v for k, v in test_pillar.items() if k == minion_id_1
    }

    res = pr.get([param1, param2, param3])
    assert res == {
        minion_id_1: {
            param1: test_pillar[minion_id_1]['1']['2']['3'],
            param2: test_pillar[minion_id_1]['1']['2']['5'],
            param3: MISSED
        }
    }


def test_pillar_updater_ensure_exists(tmpdir_function):
    pu = PillarUpdater()

    f1 = tmpdir_function / 'aaa'
    pu.ensure_exists(f1)
    assert f1.exists()

    # parent dir not exists
    f2 = tmpdir_function / 'some-dir' / 'aaa'
    pu.ensure_exists(f2)
    assert f2.parent.exists()
    assert f2.exists()


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.patch_logging([(pillar, ('error',))])
def test_pillar_updater_update_values(
    some_param_gr, test_pillar, patch_logging
):
    fpath = some_param_gr.param_spec('attr1').fpath.name

    # UNCHANGED
    pu = PillarUpdater()
    pu.update(some_param_gr(UNCHANGED))
    assert pu.pillar(fpath) == {}

    # try to update again
    with pytest.raises(RuntimeError):
        pu.update(some_param_gr(UNCHANGED))

    # DEFAULT (reset)
    pu = PillarUpdater()
    with pytest.raises(NotImplementedError):
        pu.update(some_param_gr(DEFAULT))

    # UNDEFINED
    pu = PillarUpdater()
    pu.update(some_param_gr(UNDEFINED))
    assert pu.pillar(fpath) == {'1': {'2': {'3': None}}}

    # MISSED
    pu = PillarUpdater()
    with pytest.raises(ValueError):
        pu.update(some_param_gr(MISSED))

    # non special value
    pu = PillarUpdater()
    pu.update(some_param_gr('some-value'))
    assert pu.pillar(fpath) == {'1': {'2': {'3': 'some-value'}}}


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.parametrize(
    'targets', [ALL_MINIONS, 'some_minion_id'], ids=['all', 'one']
)
def test_pillar_updater_update_rollback_dump(
    targets, some_param_gr, some_param_di, pillar_dir, pillar_host_dir_tmpl
):
    if targets != ALL_MINIONS:
        pillar_dir = Path(pillar_host_dir_tmpl.format(minion_id=targets))
        pillar_dir.mkdir(parents=True)

    input_param_group = some_param_gr('new-value1', 'new-value2')
    input_param_di = some_param_di('some_key', 'new-value3')

    attr1_param = some_param_gr.param_spec('attr1')
    attr2_param = some_param_gr.param_spec('attr2')
    attr3_param = input_param_di.param_spec()

    f1 = add_pillar_merge_prefix(
        pillar_dir / attr1_param.fpath.name
    )
    f2 = add_pillar_merge_prefix(
        pillar_dir / attr2_param.fpath.name
    )
    f3 = add_pillar_merge_prefix(
        pillar_dir / attr3_param.fpath.name
    )

    pillar_data = {'1': {'2': {'3': '4', '5': '6'}, 'di_parent': {}}}
    dump_yaml(f1, pillar_data)
    dump_yaml(f2, pillar_data)
    dump_yaml(f3, pillar_data)

    pu = PillarUpdater(targets=targets)

    # update (in memory only)
    pu.update(input_param_group, input_param_di)

    p1 = deepcopy(pillar_data)
    p1['1']['2']['3'] = input_param_group.attr1
    assert pu.pillar(f1.name) == p1
    assert load_yaml(f1) == pillar_data

    p2 = deepcopy(pillar_data)
    p2['1']['2']['5'] = input_param_group.attr2
    assert pu.pillar(f2.name) == p2
    assert load_yaml(f2) == pillar_data

    p3 = deepcopy(pillar_data)
    p3['1']['di_parent'] = {input_param_di.key_attr: input_param_di.value_attr}
    assert pu.pillar(f3.name) == p3
    assert load_yaml(f3) == pillar_data

    # update on disk
    pu.dump()
    assert load_yaml(f1) == p1
    assert load_yaml(f2) == p2
    assert load_yaml(f3) == p3

    # rolllback (in memory only)
    pu.rollback()
    assert pu.pillar(f1.name) == pillar_data
    assert load_yaml(f1) == p1

    assert pu.pillar(f2.name) == pillar_data
    assert load_yaml(f2) == p2

    assert pu.pillar(f3.name) == pillar_data
    assert load_yaml(f3) == p3

    # rollback on disk
    pu.dump()
    assert load_yaml(f1) == pillar_data
    assert load_yaml(f2) == pillar_data
    assert load_yaml(f3) == pillar_data


def test_pillar_updater_refresh(monkeypatch):

    pillar_refresh_called = 0

    def pillar_refresh(*args, **kwargs):
        nonlocal pillar_refresh_called
        pillar_refresh_called += 1

    monkeypatch.setattr(
        pillar, 'pillar_refresh', pillar_refresh
    )

    PillarUpdater.refresh()
    assert pillar_refresh_called == 1


def test_pillar_updater_component_pillar(monkeypatch, tmpdir_function):
    mock_res = []

    some_pillar = {
        1: {
            2: 3,
            4: [5, 6]
        }
    }

    default_pillar_dir = tmpdir_function / 'default'
    user_pillar_dir = tmpdir_function / 'user'

    monkeypatch.setattr(pillar, 'PRVSNR_PILLAR_DIR', default_pillar_dir)
    monkeypatch.setattr(
        pillar, 'PRVSNR_USER_PILLAR_ALL_HOSTS_DIR', user_pillar_dir
    )

    monkeypatch.setattr(
        pillar, 'dump_yaml', mock_fun_echo(mock_res, 'dump_yaml')
    )

    monkeypatch.setattr(
        pillar, 'load_yaml', mock_fun_echo(mock_res, 'load_yaml')
    )

    component = 'component1'
    default_pillar_path = (
        default_pillar_dir / 'components/{}.sls'.format(component)
    )
    user_pillar_path = user_pillar_dir / '{}.sls'.format(component)

    # show (no user pillar)
    _ = PillarUpdater().component_pillar(component, show=True)
    assert [res.key for res in mock_res] == ['load_yaml']
    assert mock_res[0].args_all == ((default_pillar_path,), {})

    # show (with user pillar)
    mock_res[:] = []
    PillarUpdater.ensure_exists(user_pillar_path)
    _ = PillarUpdater().component_pillar(component, show=True)
    assert [res.key for res in mock_res] == ['load_yaml']
    assert mock_res[0].args_all == ((user_pillar_path,), {})

    # reset for existent
    _ = PillarUpdater().component_pillar(component, reset=True)
    assert not user_pillar_path.exists()

    # reset for non-existent won't fail
    _ = PillarUpdater().component_pillar(component, reset=True)

    # set
    mock_res[:] = []
    component = 'component2'
    user_pillar_path = user_pillar_dir / '{}.sls'.format(component)
    _ = PillarUpdater().component_pillar(component, pillar=some_pillar)
    assert user_pillar_path.exists()
    assert [res.key for res in mock_res] == ['dump_yaml']
    assert mock_res[0].args_all == ((user_pillar_path, some_pillar), {})
