import pytest
import attr
import builtins
import typing

from provisioner.errors import (
    SWUpdateError,
    SWUpdateFatalError,
    ClusterMaintenanceEnableError,
    SWStackUpdateError,
    ClusterMaintenanceDisableError
)
from provisioner import (
    pillar, commands, inputs, ALL_MINIONS
)
from provisioner.salt import State
from provisioner.values import MISSED

from .helper import mock_fun_echo, mock_fun_result


def test_run_args_types():
    assert typing.get_type_hints(commands.RunArgs) == {
        'targets': str,
        'dry_run': bool
    }


def test_run_args_base_types():
    assert typing.get_type_hints(commands.RunArgsBase) == {
        'targets': str
    }


def test_get_from_spec(monkeypatch):
    get_cmd = commands.Get.from_spec()
    assert get_cmd.params_type is inputs.ParamsList

    class ParamsListChild(inputs.ParamsList):
        pass

    monkeypatch.setattr(
        inputs, 'ParamsListChild', ParamsListChild, raising=False
    )

    get_cmd = commands.Get.from_spec(params_type='ParamsListChild')
    assert get_cmd.params_type is ParamsListChild


def test_get_run(test_pillar, param_spec):
    get_cmd = commands.Get.from_spec()
    param1 = 'some_param_gr/attr1'
    param2 = 'some_param_gr/attr2'
    param3 = 'some_param_gr2/attr1/8'
    param4 = 'some_param_gr2/attr1/some_key'

    get_cmd = commands.Get()
    res = get_cmd.run(str(param1), str(param2), str(param3), str(param4))

    _iter = iter(test_pillar)
    minion_id_1 = next(_iter)
    minion_id_2 = next(_iter)

    assert res == {
        minion_id_1: {
            param1: test_pillar[minion_id_1]['1']['2']['3'],
            param2: test_pillar[minion_id_1]['1']['2']['5'],
            param3: MISSED,
            param4: MISSED
        }, minion_id_2: {
            param1: test_pillar[minion_id_2]['1']['2']['3'],
            param2: test_pillar[minion_id_2]['1']['2']['5'],
            param3: test_pillar[minion_id_2]['1']['di_parent']['8'],
            param4: MISSED
        }
    }


def test_set_from_spec():
    states = {
        'pre': [
            'some.pre.state'
        ],
        'post': [
            'some.post.state'
        ],
    }
    get_cmd = commands.Set.from_spec(params_type='NTP', states=states)
    assert get_cmd.params_type is inputs.NTP
    assert get_cmd.pre_states == [State(st) for st in states['pre']]
    assert get_cmd.post_states == [State(st) for st in states['post']]


@pytest.mark.patch_logging([(commands, ('error',))])
def test_set_run(monkeypatch, some_param_gr, patch_logging):
    pre_states = [State('pre')]
    post_states = [State('post')]

    @attr.s(auto_attribs=True)
    class SomeParamGroup(some_param_gr):
        attr3: str = inputs.ParamGroupInputBase._attr_ib(
            some_param_gr._param_group, default=''
        )

        @attr3.validator
        def _check_attr3(self, attribute, value):
            if type(value) is not str:
                raise TypeError('attr3 should be str')

    set_cmd = commands.Set(SomeParamGroup, pre_states, post_states)
    input_param = SomeParamGroup('new-value1', 'new-value2')

    calls = []

    apply_error = None
    post_apply_error = None

    # TODO consider to use mocks (e.g. pytest-mock plugin)
    @attr.s(auto_attribs=True)
    class PillarUpdater:
        targets: str = ALL_MINIONS

        def update(self, *args, **kwargs):
            calls.append((PillarUpdater.update, args, kwargs))

        def apply(self, *args, **kwargs):
            nonlocal apply_error
            calls.append((PillarUpdater.apply, args, kwargs))
            if apply_error:
                _error = apply_error
                apply_error = None
                raise _error

        def rollback(self, *args, **kwargs):
            calls.append((PillarUpdater.rollback, args, kwargs))

    class StatesApplier:
        @staticmethod
        def apply(*args, **kwargs):
            nonlocal post_apply_error
            calls.append((StatesApplier.apply, args, kwargs))
            if post_apply_error and args == (post_states,):
                _error = post_apply_error
                post_apply_error = None
                raise _error

    monkeypatch.setattr(
        commands, 'PillarUpdater', PillarUpdater
    )

    monkeypatch.setattr(
        commands, 'StatesApplier', StatesApplier
    )

    # dry run
    #   performs validation
    with pytest.raises(TypeError) as excinfo:
        set_cmd.run(1, 2, 3, dry_run=True)
    assert str(excinfo.value) == 'attr3 should be str'
    assert not calls

    #   performs validation
    set_cmd.run(input_param, dry_run=True)
    assert not calls

    # happy path
    set_cmd.run(input_param)
    assert calls == [
        (PillarUpdater.update, (input_param,), {}),
        (StatesApplier.apply, (pre_states,), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
    ]

    return

    # error during refresh
    calls[:] = []
    apply_error = RuntimeError

    with pytest.raises(apply_error):
        set_cmd.run(input_param)

    assert calls == [
        (PillarUpdater.update, (input_param,), {}),
        (StatesApplier.apply, (pre_states,), {}),
        (PillarUpdater.apply, (), {}),
        (PillarUpdater.rollback, (), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
    ]

    # error during post apply
    calls[:] = []
    apply_error = None
    post_apply_error = KeyError

    with pytest.raises(post_apply_error):
        set_cmd.run(input_param)

    assert calls == [
        (PillarUpdater.update, (input_param,), {}),
        (StatesApplier.apply, (pre_states,), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
        (PillarUpdater.rollback, (), {}),
        (PillarUpdater.apply, (), {}),
        (StatesApplier.apply, (post_states,), {}),
    ]


@pytest.fixture
def mock_eosupdate(mocker):
    calls = {}
    mocks = {}
    mock_manager = mocker.MagicMock()

    for fun in (
        'YumRollbackManager',
        'StatesApplier',
        'cluster_maintenance_enable',
        'cluster_maintenance_disable',
        'config_salt_master',
        'config_salt_minions',
        'ensure_salt_master_is_running'
    ):
        mock = mocker.patch.object(commands, fun, autospec=True)
        # TODO IMPROVE ??? is it documented somewhere - patch returns
        #       <class 'function'> but not a Mock child for functions
        #       or methods if autpospec is True
        #      (https://github.com/python/cpython/blob/3.6/Lib/unittest/mock.py#L2185-L2188)  # noqa: E501
        #      but the mock is available as `.mock` property
        #      (https://github.com/python/cpython/blob/3.6/Lib/unittest/mock.py#L188)
        mock = mock if isinstance(mock, mocker.Mock) else mock.mock
        mock_manager.attach_mock(mock, fun)
        calls[fun] = getattr(mocker.call, fun)
        mocks[fun] = mock

    mocks['rollback_ctx'] = mocks[
        'YumRollbackManager'
    ].return_value.__enter__.return_value

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=None
    )

    return (mock_manager, mocks, calls)


@pytest.mark.patch_logging([(commands, ('info',))])
def test_eosupdate_run_happy_path(patch_logging, mocker, mock_eosupdate):
    mock_manager, mocks, calls = mock_eosupdate

    # happy path
    commands.EOSUpdate().run('some-target')
    expected_calls = [
        calls['StatesApplier'].apply(
            ["components.misc_pkgs.eosupdate.repo"], 'some-target'
        ),
        calls['YumRollbackManager']('some-target', multiple_targets_ok=True),
        calls['YumRollbackManager']().__enter__(),
        calls['cluster_maintenance_enable'](),
        calls['StatesApplier'].apply(
            ["components.provisioner.update"], 'some-target'
        ),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['StatesApplier'].apply(
            ["components.{}.update".format(component)], 'some-target'
        ) for component in ('eoscore', 's3server', 'hare', 'sspl', 'csm')
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['YumRollbackManager']().__exit__(None, None, None)
    ]
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
def test_eosupdate_run_maintenance_enable_failed(
    patch_logging, mocker, mock_eosupdate
):
    mock_manager, mocks, calls = mock_eosupdate

    update_lower_exc = TypeError('some-error')
    mocks['cluster_maintenance_enable'].side_effect = update_lower_exc
    with pytest.raises(SWUpdateError) as excinfo:
        commands.EOSUpdate().run('some-target')
    exc = excinfo.value
    assert type(exc) is SWUpdateError
    assert type(exc.reason) is ClusterMaintenanceEnableError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is None
    expected_calls = [
        calls['StatesApplier'].apply(
            ["components.misc_pkgs.eosupdate.repo"], 'some-target'
        ),
        calls['YumRollbackManager']('some-target', multiple_targets_ok=True),
        calls['YumRollbackManager']().__enter__(),
        calls['cluster_maintenance_enable'](),
        calls['YumRollbackManager']().__exit__(
            ClusterMaintenanceEnableError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['cluster_maintenance_disable'](background=True),
    ]
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "rollback_error",
    [None, ValueError('some-rollback-error')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_eosupdate_run_sw_stack_update_failed(
    patch_logging, mocker, mock_eosupdate, rollback_error
):
    mock_manager, mocks, calls = mock_eosupdate
    update_lower_exc = TypeError('some-error')

    # TODO IMPROVE parametrize to emulate errors on different stages:
    #      - during provisioner update
    #      - during salt master confrig (first time and on rollback)
    #      - during salt minions confrig (first time and on rollback)
    #      - ensure_salt_master_is_running on rollback
    def apply_side_effect(states, *args, **kwargs):
        if states == ['components.eoscore.update']:
            raise update_lower_exc
        else:
            return mocker.DEFAULT

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['StatesApplier'].apply.side_effect = apply_side_effect
    expected_exc_t = SWUpdateFatalError if rollback_error else SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.EOSUpdate().run('some-target')
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is SWStackUpdateError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['StatesApplier'].apply(
            ["components.misc_pkgs.eosupdate.repo"], 'some-target'
        ),
        calls['YumRollbackManager']('some-target', multiple_targets_ok=True),
        calls['YumRollbackManager']().__enter__(),
        calls['cluster_maintenance_enable'](),
        calls['StatesApplier'].apply(
            ["components.provisioner.update"], 'some-target'
        ),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
        calls['StatesApplier'].apply(
            ["components.eoscore.update"], 'some-target'
        ),
        calls['YumRollbackManager']().__exit__(
            SWStackUpdateError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
    ]

    if rollback_error is None:
        expected_calls.extend([
            calls['ensure_salt_master_is_running'](),
            calls['config_salt_master'](),
            calls['config_salt_minions'](),
            calls['StatesApplier'].apply(
                ["components.provisioner.config"], 'some-target'
            ),
            calls['cluster_maintenance_disable']()
        ])
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "rollback_error",
    [None, ValueError('some-rollback-error')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_eosupdate_run_maintenance_disable_failed(
    patch_logging, mocker, mock_eosupdate, rollback_error
):
    mock_manager, mocks, calls = mock_eosupdate
    update_lower_exc = TypeError('some-error')

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['cluster_maintenance_disable'].side_effect = [
        update_lower_exc, mocker.DEFAULT
    ]
    expected_exc_t = SWUpdateFatalError if rollback_error else SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.EOSUpdate().run('some-target')
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is ClusterMaintenanceDisableError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['StatesApplier'].apply(
            ["components.misc_pkgs.eosupdate.repo"], 'some-target'
        ),
        calls['YumRollbackManager']('some-target', multiple_targets_ok=True),
        calls['YumRollbackManager']().__enter__(),
        calls['cluster_maintenance_enable'](),
        calls['StatesApplier'].apply(
            ["components.provisioner.update"], 'some-target'
        ),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['StatesApplier'].apply(
            ["components.{}.update".format(component)], 'some-target'
        ) for component in ('eoscore', 's3server', 'hare', 'sspl', 'csm')
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['YumRollbackManager']().__exit__(
            ClusterMaintenanceDisableError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
    ]

    if rollback_error is None:
        expected_calls.extend([
            calls['ensure_salt_master_is_running'](),
            calls['config_salt_master'](),
            calls['config_salt_minions'](),
            calls['StatesApplier'].apply(
                ["components.provisioner.config"], 'some-target'
            ),
            calls['cluster_maintenance_disable']()
        ])

    assert mock_manager.mock_calls == expected_calls


post_rollback_stages = [
    'ensure_salt_master_is_running',
    'config_salt_master',
    'config_salt_minions',
    'cluster_maintenance_disable'
]


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "post_rollback_stage_idx",
    range(len(post_rollback_stages)),
    ids=post_rollback_stages
)
def test_eosupdate_run_post_rollback_fail(
    patch_logging, mocker, mock_eosupdate, post_rollback_stage_idx
):
    mock_manager, mocks, calls = mock_eosupdate
    _idx = post_rollback_stage_idx
    update_lower_exc = TypeError('some-error')
    post_rollback_exc = ValueError('some-post-rollback-error')

    # Note. just emulate sw update on early stage
    #       since it's not an object of testing here
    def apply_side_effect(states, *args, **kwargs):
        if states == ['components.provisioner.update']:
            raise update_lower_exc
        else:
            return mocker.DEFAULT

    mocks['StatesApplier'].apply.side_effect = apply_side_effect
    mocks[post_rollback_stages[_idx]].side_effect = post_rollback_exc

    with pytest.raises(SWUpdateFatalError) as excinfo:
        commands.EOSUpdate().run('some-target')

    exc = excinfo.value
    assert type(exc) is SWUpdateFatalError
    assert type(exc.reason) is SWStackUpdateError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is post_rollback_exc

    expected_calls = [
        calls['StatesApplier'].apply(
            ["components.misc_pkgs.eosupdate.repo"], 'some-target'
        ),
        calls['YumRollbackManager']('some-target', multiple_targets_ok=True),
        calls['YumRollbackManager']().__enter__(),
        calls['cluster_maintenance_enable'](),
        calls['StatesApplier'].apply(
            ["components.provisioner.update"], 'some-target'
        ),
        calls['YumRollbackManager']().__exit__(
            SWStackUpdateError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        )
    ]

    expected_calls.extend([
        calls[stage]() for stage in post_rollback_stages[:(_idx + 1)]
    ])

    # TODO IMPROVE
    if post_rollback_stages[_idx] == 'cluster_maintenance_disable':
        expected_calls.insert(
            -1, calls['StatesApplier'].apply(
                ["components.provisioner.config"], 'some-target'
            )
        )

    assert mock_manager.mock_calls == expected_calls


def test_configure_eos(monkeypatch):
    mock_res = []

    some_pillar = {
        1: {
            2: 3,
            4: [5, 6]
        }
    }

    monkeypatch.setattr(
        commands, 'dump_yaml_str', mock_fun_echo(mock_res, 'dump_yaml_str')
    )

    monkeypatch.setattr(
        commands, 'load_yaml', mock_fun_result(
            lambda *args, **kwargs: some_pillar, mock_res, 'load_yaml'
        )
    )

    monkeypatch.setattr(
        builtins, 'print', mock_fun_echo(mock_res, 'print')
    )

    monkeypatch.setattr(
        pillar.PillarUpdater, 'component_pillar',
        mock_fun_echo(mock_res, 'component_pillar')
    )

    cmd = commands.ConfigureEOS()

    component = 'component1'

    # show
    cmd.run(component, show=True)
    assert [res.key for res in mock_res] == [
        'component_pillar', 'dump_yaml_str', 'print'
    ]
    component_pillar_res = (
        (component,), dict(show=True, reset=False, pillar=None)
    )
    dump_yaml_str_res = ((component_pillar_res,), {})
    assert mock_res[0].args_all == component_pillar_res
    assert mock_res[1].args_all == dump_yaml_str_res
    assert mock_res[2].args_all == ((dump_yaml_str_res,), {})

    # reset
    mock_res[:] = []
    cmd.run(component, reset=True)
    assert [res.key for res in mock_res] == ['component_pillar']
    assert mock_res[0].args_all == (
        (component,), dict(show=False, reset=True, pillar=None)
    )

    # set
    mock_res[:] = []
    some_source = 'some_source'
    cmd.run(component, source=some_source)
    assert [res.key for res in mock_res] == [
        'load_yaml', 'component_pillar'
    ]
    assert mock_res[0].args_all == ((some_source,), {})
    assert mock_res[1].args_all == (
        (component,), dict(show=False, reset=False, pillar=some_pillar)
    )
