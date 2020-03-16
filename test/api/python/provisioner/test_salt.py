import pytest

from provisioner import salt
from provisioner.errors import SaltError
from provisioner.config import LOCAL_MINION


def generate_local_client_mock(cmd_f):
    class LocalClient:
        def cmd(self, *args, **kwargs):
            return cmd_f(*args, **kwargs)
    return LocalClient


def generate_caller_mock(cmd_f):
    class Caller:
        def cmd(self, *args, **kwargs):
            return cmd_f(*args, **kwargs)
    return Caller


@pytest.fixture(autouse=True)
def local_minion_id(monkeypatch):
    local_minion_id = 'some_local_minion_id'
    monkeypatch.setattr(
        salt, 'local_minion_id', lambda: local_minion_id
    )
    return local_minion_id


def test_salt_pillar_get(monkeypatch):
    pillar_get_args = []
    pillar_get_res = {}

    def cmd(*args, **kwargs):
        nonlocal pillar_get_args
        pillar_get_args.append(
            (args, kwargs)
        )
        return pillar_get_res

    monkeypatch.setattr(
        salt, '_salt_local_client', generate_local_client_mock(cmd)()
    )

    pillar_get_res = {'1': {'ret': {'2': '3'}, 'retcode': 0}}
    res = salt.pillar_get(targets='aaa')

    assert pillar_get_args == [
        (
            ('aaa', 'pillar.items'),
            {'arg': (), 'kwarg': None, 'full_return': True}
        )
    ]
    assert res == {'1': {'2': '3'}}


def test_salt_pillar_refresh(monkeypatch):
    pillar_refresh_args = []

    def cmd(*args, **kwargs):
        nonlocal pillar_refresh_args
        pillar_refresh_args.append(
            (args, kwargs)
        )
        return {'some-minion': 'some-data'}

    monkeypatch.setattr(
        salt, '_salt_local_client', generate_local_client_mock(cmd)()
    )

    salt.pillar_refresh(targets='aaa')
    assert pillar_refresh_args == [
        (
            ('aaa', 'saltutil.refresh_pillar'),
            {'arg': (), 'kwarg': None, 'full_return': True}
        ),
    ]


# TODO
#   - split into separate tests
#   - add tests for Caller (targets=LOCAL_MINION)
def test_salt_states_apply(monkeypatch):
    states_apply_args = []
    states_apply_res = {}

    def cmd(*args, **kwargs):
        nonlocal states_apply_args
        states_apply_args.append(
            (args, kwargs)
        )
        return states_apply_res

    monkeypatch.setattr(
        salt, '_salt_local_client', generate_local_client_mock(cmd)()
    )

    states_apply_res = {'some-node': 'some-res'}
    salt.states_apply(['state1', 'state2', 'state3'], targets='aaa')
    assert states_apply_args == [
        (
            ('aaa', 'state.apply'),
            {'arg': ['state1'], 'kwarg': None, 'full_return': True}
        ),
        (
            ('aaa', 'state.apply'),
            {'arg': ['state2'], 'kwarg': None, 'full_return': True}
        ),
        (
            ('aaa', 'state.apply'),
            {'arg': ['state3'], 'kwarg': None, 'full_return': True}
        )
    ]

    # fail case
    states_apply_res = {
        'some-node-id': {
            'ret': {
                'some-task-id': {
                    'result': False,
                    'comment': 'some comment'
                }
            },
            'retcode': 1
        }
    }
    with pytest.raises(SaltError) as excinfo:
        salt.states_apply(['state1', 'state2', 'state3'], targets='aaa')
    assert str(excinfo.value) == (
        "Failed to apply state '{}': salt command failed: {}"
        .format('state1', {'some-node-id': {'some-task-id': 'some comment'}})
    )

    # success case
    states_apply_res['some-node-id']['retcode'] = 0
    res = salt.states_apply(['some.state'], targets='aaa')
    assert res == {
        'some.state': {'some-node-id': states_apply_res['some-node-id']['ret']}
    }


def test_salt_state_fun_execute(monkeypatch, local_minion_id):
    caller_args = []
    caller_res = {}

    local_client_args = []
    local_client_res = {}

    def cmd_caller(*args, **kwargs):
        nonlocal caller_args
        caller_args.append(
            (args, kwargs)
        )
        return caller_res

    def cmd_local(*args, **kwargs):
        nonlocal local_client_args
        local_client_args.append(
            (args, kwargs)
        )
        return local_client_res

    monkeypatch.setattr(
        salt, '_salt_local_client', generate_local_client_mock(cmd_local)()
    )
    monkeypatch.setattr(
        salt, '_salt_caller', generate_caller_mock(cmd_caller)()
    )

    local_client_args = []
    local_client_res = {'some-res'}
    salt.state_fun_execute(
        'state_fun1',
        fun_args=['some_arg'],
        fun_kwargs=dict(some_kwarg=1),
        targets='aaa'
    )
    assert local_client_args == [
        (
            ('aaa', 'state.single'),
            {
                'arg': ['state_fun1', 'some_arg'],
                'kwarg': {'some_kwarg': 1},
                'full_return': True
            }
        )
    ]

    local_client_args = []
    salt.state_fun_execute(
        'state_fun1',
        fun_args=['some_arg'],
        fun_kwargs=dict(some_kwarg=1),
        targets=LOCAL_MINION
    )
    assert local_client_args == [
        (
            (local_minion_id, 'state.single'),
            {
                'arg': ['state_fun1', 'some_arg'],
                'kwarg': {'some_kwarg': 1},
                'full_return': True
            }
        ),
    ]

    # fail case
    local_client_res = {
        'some-node-id': {
            'ret': {
                'some-task-id': {
                    'result': False,
                    'comment': 'some comment'
                }
            },
            'retcode': 1
        }
    }
    with pytest.raises(SaltError) as excinfo:
        salt.state_fun_execute(
            'state_fun1',
            fun_args=['some_arg'],
            fun_kwargs=dict(some_kwarg=1),
            targets='aaa'
        )
    assert str(excinfo.value) == (
        "Failed to execute state function '{}': salt command failed: {}"
        .format(
            'state_fun1',
            {'some-node-id': {'some-task-id': 'some comment'}}
        )
    )
    with pytest.raises(SaltError) as excinfo:
        salt.state_fun_execute(
            'state_fun1',
            fun_args=['some_arg'],
            fun_kwargs=dict(some_kwarg=1),
            targets=LOCAL_MINION
        )
    assert str(excinfo.value) == (
        "Failed to execute state function '{}': salt command failed: {}"
        .format(
            'state_fun1', {'some-node-id': {'some-task-id': 'some comment'}}
        )
    )

    # success case
    local_client_res['some-node-id']['retcode'] = 0
    # local_client_res['some-node-id']['ret']['some-task-id']['result'] = True
    res = salt.state_fun_execute(
        'some.state',
        fun_args=['some_arg'],
        fun_kwargs=dict(some_kwarg=1),
        targets='aaa'
    )
    assert res == {
        'some-node-id': local_client_res['some-node-id']['ret']
    }
    res = salt.state_fun_execute(
        'some.state',
        fun_args=['some_arg'],
        fun_kwargs=dict(some_kwarg=1),
        targets=LOCAL_MINION
    )
    assert res == {
        'some-node-id': local_client_res['some-node-id']['ret']
    }
