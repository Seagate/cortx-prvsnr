import pytest

from provisioner import salt
from provisioner.errors import SaltError


def generate_mock_class(cmd_f):
    class LocalClient:
        def cmd(self, *args, **kwargs):
            return cmd_f(*args, **kwargs)
    return LocalClient


def test_salt_pillar_get(monkeypatch):
    pillar_get_args = []
    pillar_get_res = {}

    def cmd(*args, **kwargs):
        nonlocal pillar_get_args
        pillar_get_args.append(
            (args, kwargs)
        )
        return pillar_get_res

    monkeypatch.setattr(salt, 'LocalClient', generate_mock_class(cmd))

    pillar_get_res = {'1': {'ret': {'2': '3'}, 'retcode': 0}}
    res = salt.pillar_get(targets='aaa')

    assert pillar_get_args == [
        (('aaa', 'pillar.items'), {'full_return': True}),
    ]
    assert res == {'1': {'2': '3'}}


def test_salt_pillar_refresh(monkeypatch):
    pillar_refresh_args = []

    def cmd(*args, **kwargs):
        nonlocal pillar_refresh_args
        pillar_refresh_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(salt, 'LocalClient', generate_mock_class(cmd))

    salt.pillar_refresh(targets='aaa')
    assert pillar_refresh_args == [
        (('aaa', 'saltutil.refresh_pillar'), {'full_return': True}),
    ]


# TODO split into separate tests
def test_salt_states_apply(monkeypatch):
    states_apply_args = []
    states_apply_res = {}

    def cmd(*args, **kwargs):
        nonlocal states_apply_args
        states_apply_args.append(
            (args, kwargs)
        )
        return states_apply_res

    monkeypatch.setattr(salt, 'LocalClient', generate_mock_class(cmd))

    states_apply_res = None
    salt.states_apply(['state1', 'state2', 'state3'], targets='aaa')
    assert states_apply_args == [
        (('aaa', 'state.apply', ['state1']), {'full_return': True}),
        (('aaa', 'state.apply', ['state2']), {'full_return': True}),
        (('aaa', 'state.apply', ['state3']), {'full_return': True})
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
