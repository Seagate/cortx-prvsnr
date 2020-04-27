import pytest
from copy import deepcopy
from pathlib import Path

from provisioner.utils import dump_yaml, load_yaml
from provisioner.param import Param
from provisioner import (
    pillar, ALL_MINIONS, UNCHANGED, DEFAULT, MISSED, UNDEFINED
)
from provisioner.pillar import (
    PillarEntry, PillarResolver, PillarUpdater
)

from .helper import mock_fun_echo


def test_pillar_entry_get():
    pillar = {'1': {'2': '3'}}

    assert PillarEntry('1/2', pillar).get() == '3'
    assert PillarEntry('1/4', pillar).get() == MISSED


def test_pillar_entry_set():
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


def test_pillar_entry_rollback():
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
    param1 = Param('some-param', 'aaa.sls', '1/2/3')
    param2 = Param('some-param2', 'aaa.sls', '1/2/5')
    param3 = Param('some-param2', 'aaa.sls', '1/di_parent/8')

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


@pytest.mark.patch_logging([(pillar, ('error',))])
def test_pillar_updater_update_values(
    some_param_gr, test_pillar, patch_logging
):
    fpath = some_param_gr.param_spec('attr1').pi_path.name

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

    f1 = pillar_dir / attr1_param.pi_path.name
    f2 = pillar_dir / attr2_param.pi_path.name
    f3 = pillar_dir / attr3_param.pi_path.name

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
        pillar, 'PRVSNR_USER_PI_ALL_HOSTS_DIR', user_pillar_dir
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
