import pytest

from api.python.provisioner import _api as api
from api.python.provisioner.errors import UnknownParamError
from api.python.provisioner.utils import load_yaml


# TODO test utils


@pytest.fixture(autouse=True)
def pillar_dir(monkeypatch, tmpdir_function):
    pillar_dir = tmpdir_function / 'pillar'
    monkeypatch.setattr(api, 'PRVSNR_USER_PILLAR_DIR', pillar_dir)
    return pillar_dir


def test_api_get_params_fails_for_unknown_param(monkeypatch):
    monkeypatch.setattr(api, 'prvsnr_params', {})
    with pytest.raises(UnknownParamError):
        api.get_params('some-param')


def test_api_get_params_succeeds(monkeypatch):
    data = {'1': {'2': {'3': '4', '5': '6'}}}

    def pillar_get(*args, **kwargs):
        return {'some-node-id': data}

    monkeypatch.setattr(
        api, 'prvsnr_params', {
            'some-param': {
                'pillar': {
                    'key_path': ('1', '2', '3')
                }
            },
            'some-param2': {
                'pillar': {
                    'key_path': ('1', '2', '5')
                }
            }
        }
    )

    monkeypatch.setattr(
        api, 'pillar_get', pillar_get
    )

    # test single ones
    assert api.get_params('some-param') == {'some-param': '4'}
    assert api.get_params('some-param2') == {'some-param2': '6'}
    # test multiple
    assert api.get_params('some-param', 'some-param2') == {
        'some-param': '4', 'some-param2': '6'
    }


def test_api_set_params_fails_for_unknown_param(monkeypatch):
    monkeypatch.setattr(api, 'prvsnr_params', {})
    with pytest.raises(UnknownParamError):
        api.set_params(some_param=1)


def test_api_set_params_succeeds(monkeypatch, pillar_dir):
    pillar_refresh_called = 0
    states_apply_args = []

    def pillar_refresh(*args, **kwargs):
        nonlocal pillar_refresh_called
        pillar_refresh_called += 1

    def states_apply(*args, **kwargs):
        nonlocal states_apply_args
        states_apply_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        api, 'pillar_refresh', pillar_refresh
    )
    monkeypatch.setattr(
        api, 'states_apply', states_apply
    )

    test_pillar = 'aaa/bbb/test.sls'
    test_pillar_path = pillar_dir / test_pillar

    monkeypatch.setattr(
        api, 'prvsnr_params', {
            'some-param': {
                'states': {
                    'pre': [
                        'pre_state'
                    ],
                    'post': [
                        'post_state'
                    ],
                },
                'pillar': {
                    'path': str(test_pillar),
                    'key_path': ('1', '2', '3')
                }
            },
            'some-param2': {
                'states': {
                    'post': [
                        'post_state2'
                    ],
                },
                'pillar': {
                    'path': str(test_pillar),
                    'key_path': ('1', '4')
                }
            }
        }
    )

    api.set_params(**{'some-param': 'some-value'})

    # check that pillar file is created with expected data
    assert test_pillar_path.exists()
    pillar = load_yaml(test_pillar_path)
    assert pillar == {'1': {'2': {'3': 'some-value'}}}

    # TODO check the order: pre_states - pillar-update - refresh - post states
    # check that expected states were called
    assert states_apply_args == [
        (tuple(), {'states': ['pre_state'], 'targets': '*'}),
        (tuple(), {'states': ['post_state'], 'targets': '*'}),
    ]

    # check that refreshpillar was called
    assert pillar_refresh_called == 1

    # repeate the same but dir is already exists now
    test_pillar_path.unlink()
    api.set_params(**{'some-param': 'some-value'})

    # check that pillar file is updated
    api.set_params(**{'some-param': 'some-new-value'})
    pillar = load_yaml(test_pillar_path)
    assert pillar == {'1': {'2': {'3': 'some-new-value'}}}

    pillar_refresh_called = False
    states_apply_args = []
    # check multiple updates
    api.set_params(**{'some-param': 'value1', 'some-param2': 'value2'})
    pillar = load_yaml(test_pillar_path)
    assert pillar == {
        '1': {'2': {'3': 'value1'}, '4': 'value2'}
    }
    assert pillar_refresh_called == 2
    # TODO better check
    for item in [
        (tuple(), {'states': ['pre_state'], 'targets': '*'}),
        (tuple(), {'states': ['post_state'], 'targets': '*'}),
        (tuple(), {'states': ['post_state2'], 'targets': '*'}),
    ]:
        assert item in states_apply_args
