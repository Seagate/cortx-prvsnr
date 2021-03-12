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
import builtins
import typing
import functools

from provisioner.vendor import attr
from provisioner.errors import (
    PillarSetError,
    SWUpdateError,
    SWUpdateFatalError,
    ClusterMaintenanceEnableError,
    SWStackUpdateError,
    ClusterMaintenanceDisableError,
    HAPostUpdateError,
    ClusterNotHealthyError
)
from provisioner import config
from provisioner import (
    pillar, commands, inputs, ALL_MINIONS
)
from provisioner.salt import State, YumRollbackManager
from provisioner.values import MISSED

from .helper import mock_fun_echo, mock_fun_result


# HELPERS and FIXTURE

@pytest.fixture(scope='module')
def fw_source(tmpdir_module):
    fw_source = tmpdir_module / 'somefile'
    fw_source.touch()
    return fw_source


@pytest.fixture(scope='module')
def controller_cli_script():
    return (
        config.PRVSNR_FILEROOT_DIR /
        'components/controller/files/scripts/controller-cli.sh'
    )


@pytest.fixture
def storage_enclosure_data(mocker):
    ip = '1.2.3.4'
    user = 'someuser'
    passwd = 'somepasswd'

    test_pillar = dict(someminionid={
        "storage": {
            "enclosure-1": {
                "controller": {
                    "primary": {
                        "ip": f"{ip}"
                    },
                    "secondary": {
                        "ip": f"{ip}"
                    },
                    "user": f"{user}",
                    "secret": f"{passwd}"
                }
            }
        }
    })

    mocker.patch.object(
        pillar, 'pillar_get', autospec=True, return_value=test_pillar
    )

    return (ip, user, passwd)


@pytest.fixture
def state_fun_executer_m(mocker):
    return mocker.patch.object(
        commands, 'StateFunExecuter', autospec=True
    )


# ### PillarGet ###

def test_commands_RunArgs_types():
    assert typing.get_type_hints(commands.RunArgs) == {
        'targets': str,
        'dry_run': bool
    }


def test_commands_RunArgs_base_types():
    assert typing.get_type_hints(commands.RunArgsBase) == {
        'targets': str
    }


def test_commands_PillarGet_from_spec(monkeypatch):
    get_cmd = commands.PillarGet.from_spec()
    assert get_cmd.input_type is inputs.PillarKeysList

    class PillarKeysListChild(inputs.PillarKeysList):
        pass

    monkeypatch.setattr(
        inputs, 'PillarKeysListChild', PillarKeysListChild, raising=False
    )

    get_cmd = commands.PillarGet.from_spec(input_type='PillarKeysListChild')
    assert get_cmd.input_type is PillarKeysListChild


def test_commands_PillarGet_run(test_pillar):
    get_cmd = commands.PillarGet.from_spec()

    # all pillar
    assert get_cmd.run() == test_pillar

    # specific keys
    pi_key1 = '1/2/3'
    pi_key2 = '1/2/5'
    pi_key3 = '1/di_parent/8'
    pi_key4 = '1/di_parent/some_key'

    get_cmd = commands.PillarGet()
    res = get_cmd.run(pi_key1, pi_key2, pi_key3, pi_key4)

    _iter = iter(test_pillar)
    minion_id_1 = next(_iter)
    minion_id_2 = next(_iter)

    assert res == {
        minion_id_1: {
            pi_key1: test_pillar[minion_id_1]['1']['2']['3'],
            pi_key2: test_pillar[minion_id_1]['1']['2']['5'],
            pi_key3: MISSED,
            pi_key4: MISSED
        }, minion_id_2: {
            pi_key1: test_pillar[minion_id_2]['1']['2']['3'],
            pi_key2: test_pillar[minion_id_2]['1']['2']['5'],
            pi_key3: test_pillar[minion_id_2]['1']['di_parent']['8'],
            pi_key4: MISSED
        }
    }


# ### PillarSet ###

def test_commands_PillarSet_from_spec(monkeypatch):
    get_cmd = commands.PillarSet.from_spec()
    assert get_cmd.input_type is inputs.PillarInputBase

    class PillarInputChild(inputs.PillarInputBase):
        pass

    monkeypatch.setattr(
        inputs, 'PillarInputChild', PillarInputChild, raising=False
    )

    get_cmd = commands.PillarSet.from_spec(input_type='PillarInputChild')
    assert get_cmd.input_type is PillarInputChild


@pytest.mark.patch_logging([(commands, ('error',))])
def test_commands_PillarSet_run_dry_run(patch_logging, mocker):
    # TODO IMPROVE OR TODO DOC
    # - PillarSet uses isinstance and it fails for PillarInputBase mocks:
    #       TypeError: isinstance() arg 2 must be a type or tuple of types
    #   options: mock only just 'from_args' method
    #       - with autospec=True fails since classmethods
    #         mocks are not callable for older version of mocker
    #       - WORKS with autospec=False
    from_args_m = mocker.patch.object(
        commands.inputs.PillarInputBase, 'from_args'
    )
    pillar_updater_m = mocker.patch.object(
        commands, 'PillarUpdater', autospec=True
    )

    set_cmd = commands.PillarSet()

    keypath, value, fpath = '1/2/3', 456, '789.sls'

    # inputs as first arg object
    input_data = set_cmd.input_type(keypath, value, fpath=fpath)
    set_cmd.run(input_data, dry_run=True)

    from_args_m.assert_not_called()
    pillar_updater_m.assert_not_called()

    # inputs as a set of attrs
    set_cmd.run(keypath, value, fpath=fpath, dry_run=True)
    from_args_m.assert_called_once_with(keypath, value, fpath=fpath)
    pillar_updater_m.assert_not_called()


@pytest.mark.patch_logging([(commands, ('error',))])
def test_commands_PillarSet_run_happy_path(patch_logging, mocker):
    pillar_updater_m = mocker.patch.object(
        commands, 'PillarUpdater', autospec=True
    )

    keypath, value, fpath = '1/2/3', 456, '789.sls'
    targets = 'some-target'

    inputs = commands.inputs.PillarInputBase(keypath, value, fpath=fpath)
    set_cmd = commands.PillarSet()
    set_cmd.run(inputs, targets=targets)

    # TODO IMPROVE review mock call API for more accurate verification
    assert pillar_updater_m.mock_calls == [
        mocker.call(targets),
        mocker.call().update(inputs),
        mocker.call().apply(),
    ]


@pytest.mark.parametrize(
    'rollback_exc', [None, TypeError('someerror')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_commands_PillarSet_run_fail_pillar_apply(mocker, rollback_exc):
    mock_manager = mocker.MagicMock()

    logger_m = mocker.patch.object(
        commands, 'logger', autospec=False
    )
    pillar_updater_m = mocker.patch.object(
        commands, 'PillarUpdater', autospec=True
    )

    mock_manager.attach_mock(logger_m, 'logger')
    mock_manager.attach_mock(pillar_updater_m, 'pillar_updater')

    exc = ValueError('someerror')
    pillar_updater_m.return_value.apply.side_effect = [exc, mocker.DEFAULT]

    if rollback_exc:
        pillar_updater_m.return_value.rollback.side_effect = rollback_exc

    inputs = commands.inputs.PillarInputBase('1/2/3', 456, fpath='789.sls')
    targets = 'some-target'

    set_cmd = commands.PillarSet()

    with pytest.raises(PillarSetError) as excinfo:
        set_cmd.run(inputs, targets=targets)

    assert excinfo.value.reason is exc
    assert excinfo.value.rollback_error is rollback_exc

    expected_calls = [
        mocker.call.pillar_updater(targets),
        mocker.call.pillar_updater().update(inputs),
        mocker.call.pillar_updater().apply(),
        mocker.call.pillar_updater().rollback(),
        mocker.call.logger.exception('Pillar set failed'),
    ]

    if rollback_exc is None:
        expected_calls.insert(-1, mocker.call.pillar_updater().apply())

    # TODO IMPROVE review mock call API for more accurate verification
    assert mock_manager.mock_calls == expected_calls


# ### Get ###

def test_commands_Get_from_spec(monkeypatch):
    get_cmd = commands.Get.from_spec()
    assert get_cmd.input_type is inputs.ParamsList

    class ParamsListChild(inputs.ParamsList):
        pass

    monkeypatch.setattr(
        inputs, 'ParamsListChild', ParamsListChild, raising=False
    )

    get_cmd = commands.Get.from_spec(input_type='ParamsListChild')
    assert get_cmd.input_type is ParamsListChild


@pytest.mark.skip(reason="EOS-18738")
def test_commands_Get_run(test_pillar, param_spec):
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


def test_commands_Set_from_spec():
    states = {
        'pre': [
            'some.pre.state'
        ],
        'post': [
            'some.post.state'
        ],
    }
    get_cmd = commands.Set.from_spec(input_type='NTP', states=states)
    assert get_cmd.input_type is inputs.NTP
    assert get_cmd.pre_states == [State(st) for st in states['pre']]
    assert get_cmd.post_states == [State(st) for st in states['post']]


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.patch_logging([(commands, ('error',))])
def test_commands_Set_run(monkeypatch, some_param_gr, patch_logging):
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


@pytest.mark.patch_logging([(commands, ('info',))])
def test_commnads_ensure_update_repos_configuration(patch_logging, mocker):
    target = 'some-target'
    mocker.patch.object(commands, 'StatesApplier', autospec=True)

    commands._ensure_update_repos_configuration(target)

    mocker.call.StatesApplier.apply(
        ['components.misc_pkgs.swupdate.repo'], target
    )


@pytest.mark.patch_logging([(commands, ('info',))])
def test_commnads_pre_yum_rollback(patch_logging, mocker):
    mock = mocker.patch.object(
        commands, 'cluster_maintenance_enable', autospec=True
    )

    exc = TypeError('some error')
    commands._pre_yum_rollback('some-ctx', type(exc), exc, 'some traceback')
    mock.assert_not_called()

    for exc in (
        HAPostUpdateError('some error'),
        ClusterNotHealthyError('some error')
    ):
        mock.reset_mock()
        mock.side_effect = None
        commands._pre_yum_rollback(
            'some-ctx', type(exc), exc, 'some traceback'
        )
        mock.assert_called_once_with()

        mock.reset_mock()
        mock.side_effect = ValueError('some another error')

        with pytest.raises(ClusterMaintenanceEnableError):
            commands._pre_yum_rollback(
                'some-ctx', type(exc), exc, 'some traceback'
            )
        mock.assert_called_once_with()


@pytest.mark.patch_logging([(commands, ('info',))])
def test_commnads_update_component(patch_logging, mocker):
    target = 'some-target'
    component = 'some_component'
    mocker.patch.object(commands, 'StatesApplier', autospec=True)

    commands._update_component(component, target)

    mocker.call.StatesApplier.apply(
        [f"components.{component}.update"], target
    )


@pytest.mark.patch_logging([(commands, ('info',))])
def test_commnads_apply_provisioner_config(patch_logging, mocker):
    target = 'some-target'
    mocker.patch.object(commands, 'StatesApplier', autospec=True)

    commands._apply_provisioner_config(target)

    mocker.call.StatesApplier.apply(
        ["components.provisioner.config"], target
    )


@pytest.fixture
def mock_swupdate(mocker):
    calls = {}
    mocks = {}
    mock_manager = mocker.MagicMock()  # TODO DOC

    for fun in (
        'YumRollbackManager',
        'cluster_maintenance_enable',
        'cluster_maintenance_disable',
        'apply_ha_post_update',
        'ensure_cluster_is_healthy',
        'config_salt_master',
        'config_salt_minions',
        'ensure_salt_master_is_running',
        '_ensure_update_repos_configuration',
        '_update_component',
        '_apply_provisioner_config',
        '_consul_export',
        '_restart_salt_minions',
    ):
        mock = mocker.patch.object(commands, fun, autospec=True)
        # TODO DOC
        # TODO IMPROVE ??? is it documented somewhere - patch returns
        #       <class 'function'> but not a Mock child for functions
        #       or methods if autospec is True
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

    # TODO DOC attaching propery mock to a mock
    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=None
    )

    def _init(self, *args, **kwargs):
        for k, v in attr.asdict(YumRollbackManager(*args, **kwargs)).items():
            setattr(self, k, v)
        return mocker.DEFAULT

    def _enter(*args, **kwargs):
        YumRollbackManager.__enter__(*args, **kwargs)
        return mocker.DEFAULT

    def _exit(*args, **kwargs):
        YumRollbackManager.__exit__(*args, **kwargs)
        return mocker.DEFAULT

    mocks['YumRollbackManager'].side_effect = (
        functools.partial(
            _init, mocks['YumRollbackManager'].return_value
        )
    )

    mocks['YumRollbackManager'].return_value.__enter__.side_effect = (
        functools.partial(
            _enter, mocks['YumRollbackManager'].return_value
        )
    )

    mocks['YumRollbackManager'].return_value.__exit__.side_effect = (
        functools.partial(
            _exit, mocks['YumRollbackManager'].return_value
        )
    )

    return (mock_manager, mocks, calls)


@pytest.mark.patch_logging([(commands, ('info',))])
def test_commands_SWUpdate_run_happy_path(
    patch_logging, mocker, mock_swupdate
):
    mock_manager, mocks, calls = mock_swupdate

    target = 'some-target'

    # happy path
    commands.SWUpdate().run(target)
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['_update_component'](component, target)
        for component in (
            'motr', 's3server', 'hare', 'ha.cortx-ha', 'sspl', 'uds', 'csm'
        )
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['_consul_export']('update-pre-ha-update'),
        calls['apply_ha_post_update'](target),
        calls['_consul_export']('update-post-ha-update'),
        calls['ensure_cluster_is_healthy'](),
        calls['_consul_export']('update-post'),
        calls['config_salt_minions']().__bool__(),
        calls['_restart_salt_minions'](),
        calls['YumRollbackManager']().__exit__(None, None, None)
    ]
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
def test_commands_SWUpdate_run_pre_stages_failed(
    patch_logging, mocker, mock_swupdate
):
    mock_manager, mocks, calls = mock_swupdate
    update_lower_exc = TypeError('some-error')
    target = 'some-target'

    mocks['ensure_cluster_is_healthy'].side_effect = update_lower_exc
    expected_exc_t = SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert exc.reason is update_lower_exc
    assert exc.rollback_error is None
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
    ]
    assert mock_manager.mock_calls == expected_calls

    mock_manager.reset_mock()
    mocks['ensure_cluster_is_healthy'].side_effect = None
    mocks['_ensure_update_repos_configuration'].side_effect = update_lower_exc
    expected_exc_t = SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert exc.reason is update_lower_exc
    assert exc.rollback_error is None
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
    ]
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
def test_commands_SWUpdate_run_maintenance_enable_failed(
    patch_logging, mocker, mock_swupdate
):
    mock_manager, mocks, calls = mock_swupdate
    target = 'some-target'

    update_lower_exc = TypeError('some-error')
    mocks['cluster_maintenance_enable'].side_effect = update_lower_exc
    with pytest.raises(SWUpdateError) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is SWUpdateError
    assert type(exc.reason) is ClusterMaintenanceEnableError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is None
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['YumRollbackManager']().__exit__(
            ClusterMaintenanceEnableError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['YumRollbackManager']()._yum_rollback(),
        calls['cluster_maintenance_disable'](background=True),
    ]
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "rollback_error",
    [None, ValueError('some-rollback-error')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_commands_SWUpdate_run_sw_stack_update_failed(
    patch_logging, mocker, mock_swupdate, rollback_error
):
    mock_manager, mocks, calls = mock_swupdate
    update_lower_exc = TypeError('some-error')
    target = 'some-target'

    # TODO IMPROVE parametrize to emulate errors on different stages:
    #      - during provisioner update
    #      - during salt-master config (first time and on rollback)
    #      - during salt-minions config (first time and on rollback)
    #      - ensure_salt_master_is_running on rollback
    def apply_side_effect(component, *args, **kwargs):
        if component == 'motr':
            raise update_lower_exc
        else:
            return mocker.DEFAULT

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['_update_component'].side_effect = apply_side_effect
    expected_exc_t = SWUpdateFatalError if rollback_error else SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is SWStackUpdateError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
        calls['_update_component']("motr", target),
        calls['YumRollbackManager']().__exit__(
            SWStackUpdateError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['YumRollbackManager']()._yum_rollback(),
    ]

    if rollback_error is None:
        expected_calls.extend([
            calls['ensure_salt_master_is_running'](),
            calls['config_salt_master'](),
            calls['config_salt_minions'](),
            calls['_apply_provisioner_config'](target),
            calls['cluster_maintenance_disable'](),
            calls['_consul_export']('rollback-pre-ha-update'),
            calls['apply_ha_post_update'](target),
            calls['_consul_export']('rollback-post-ha-update'),
            calls['ensure_cluster_is_healthy'](),
            calls['_consul_export']('rollback-post'),
        ])
    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "rollback_error",
    [None, ValueError('some-rollback-error')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_commands_SWUpdate_run_maintenance_disable_failed(
    patch_logging, mocker, mock_swupdate, rollback_error
):
    mock_manager, mocks, calls = mock_swupdate
    update_lower_exc = TypeError('some-error')
    target = 'some-target'

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['cluster_maintenance_disable'].side_effect = [
        update_lower_exc, mocker.DEFAULT
    ]
    expected_exc_t = SWUpdateFatalError if rollback_error else SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is ClusterMaintenanceDisableError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['_update_component'](component, target)
        for component in (
            'motr', 's3server', 'hare', 'ha.cortx-ha', 'sspl', 'uds', 'csm'
        )
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['YumRollbackManager']().__exit__(
            ClusterMaintenanceDisableError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['YumRollbackManager']()._yum_rollback(),
    ]

    if rollback_error is None:
        expected_calls.extend([
            calls['ensure_salt_master_is_running'](),
            calls['config_salt_master'](),
            calls['config_salt_minions'](),
            calls['_apply_provisioner_config'](target),
            calls['cluster_maintenance_disable'](),
            calls['_consul_export']('rollback-pre-ha-update'),
            calls['apply_ha_post_update'](target),
            calls['_consul_export']('rollback-post-ha-update'),
            calls['ensure_cluster_is_healthy'](),
            calls['_consul_export']('rollback-post'),
        ])

    assert mock_manager.mock_calls == expected_calls


# TODO IMPROVE DRY EOS-8940 (very close to upper tests)
@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "rollback_error",
    [None, ValueError('some-rollback-error')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_commands_SWUpdate_run_ha_post_update_failed(
    patch_logging, mocker, mock_swupdate, rollback_error
):
    mock_manager, mocks, calls = mock_swupdate
    update_lower_exc = TypeError('some-error')
    target = 'some-target'

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['apply_ha_post_update'].side_effect = [
        update_lower_exc, mocker.DEFAULT
    ]
    expected_exc_t = SWUpdateFatalError if rollback_error else SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is HAPostUpdateError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['_update_component'](component, target)
        for component in (
            'motr', 's3server', 'hare', 'ha.cortx-ha', 'sspl', 'uds', 'csm'
        )
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['_consul_export']('update-pre-ha-update'),
        calls['apply_ha_post_update'](target),
        calls['YumRollbackManager']().__exit__(
            HAPostUpdateError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['cluster_maintenance_enable'](),
        calls['YumRollbackManager']()._yum_rollback(),
    ]

    if rollback_error is None:
        expected_calls.extend([
            calls['ensure_salt_master_is_running'](),
            calls['config_salt_master'](),
            calls['config_salt_minions'](),
            calls['_apply_provisioner_config'](target),
            calls['cluster_maintenance_disable'](),
            calls['_consul_export']('rollback-pre-ha-update'),
            calls['apply_ha_post_update'](target),
            calls['_consul_export']('rollback-post-ha-update'),
            calls['ensure_cluster_is_healthy'](),
            calls['_consul_export']('rollback-post'),
        ])

    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "rollback_error",
    [None, ValueError('some-rollback-error')],
    ids=['rollback_ok', 'rollback_failed']
)
def test_commands_SWUpdate_run_ensure_cluster_is_healthy_failed(
    patch_logging, mocker, mock_swupdate, rollback_error
):
    mock_manager, mocks, calls = mock_swupdate
    update_lower_exc = TypeError('some-error')
    target = 'some-target'

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['ensure_cluster_is_healthy'].side_effect = [
        mocker.DEFAULT, update_lower_exc, mocker.DEFAULT
    ]
    expected_exc_t = SWUpdateFatalError if rollback_error else SWUpdateError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is ClusterNotHealthyError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['_update_component'](component, target)
        for component in (
            'motr', 's3server', 'hare', 'ha.cortx-ha', 'sspl', 'uds', 'csm'
        )
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['_consul_export']('update-pre-ha-update'),
        calls['apply_ha_post_update'](target),
        calls['_consul_export']('update-post-ha-update'),
        calls['ensure_cluster_is_healthy'](),
        calls['YumRollbackManager']().__exit__(
            ClusterNotHealthyError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['cluster_maintenance_enable'](),
        calls['YumRollbackManager']()._yum_rollback(),
    ]

    if rollback_error is None:
        expected_calls.extend([
            calls['ensure_salt_master_is_running'](),
            calls['config_salt_master'](),
            calls['config_salt_minions'](),
            calls['_apply_provisioner_config'](target),
            calls['cluster_maintenance_disable'](),
            calls['_consul_export']('rollback-pre-ha-update'),
            calls['apply_ha_post_update'](target),
            calls['_consul_export']('rollback-post-ha-update'),
            calls['ensure_cluster_is_healthy'](),
            calls['_consul_export']('rollback-post'),
        ])

    assert mock_manager.mock_calls == expected_calls


@pytest.mark.patch_logging([(commands, ('error',))])
def test_commands_SWUpdate_run_maintenance_enable_at_rollback_failed(
    patch_logging, mocker, mock_swupdate
):
    mock_manager, mocks, calls = mock_swupdate
    update_lower_exc = TypeError('some-error')
    target = 'some-target'
    rollback_error = ValueError('some-rollback-error')

    type(mocks['rollback_ctx']).rollback_error = mocker.PropertyMock(
        return_value=rollback_error
    )

    mocks['ensure_cluster_is_healthy'].side_effect = [
        mocker.DEFAULT, update_lower_exc, mocker.DEFAULT
    ]
    mocks['cluster_maintenance_enable'].side_effect = [
        mocker.DEFAULT, rollback_error, mocker.DEFAULT
    ]
    expected_exc_t = SWUpdateFatalError
    with pytest.raises(expected_exc_t) as excinfo:
        commands.SWUpdate().run(target)
    exc = excinfo.value
    assert type(exc) is expected_exc_t
    assert type(exc.reason) is ClusterNotHealthyError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is rollback_error
    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['config_salt_master'](),
        calls['config_salt_minions'](),
    ] + [
        calls['_update_component'](component, target)
        for component in (
            'motr', 's3server', 'hare', 'ha.cortx-ha', 'sspl', 'csm', 'uds'
        )
    ] + [
        calls['cluster_maintenance_disable'](),
        calls['_consul_export']('update-pre-ha-update'),
        calls['apply_ha_post_update'](target),
        calls['_consul_export']('update-post-ha-update'),
        calls['ensure_cluster_is_healthy'](),
        calls['YumRollbackManager']().__exit__(
            ClusterNotHealthyError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['cluster_maintenance_enable'](),
    ]

    assert mock_manager.mock_calls == expected_calls


post_rollback_stages = [
    'ensure_salt_master_is_running',
    'config_salt_master',
    'config_salt_minions',
    '_apply_provisioner_config',
    'cluster_maintenance_disable',
    '_consul_export:rollback-pre-ha-update',
    'apply_ha_post_update',
    '_consul_export:rollback-post-ha-update',
    'ensure_cluster_is_healthy'
]


@pytest.mark.patch_logging([(commands, ('error',))])
@pytest.mark.parametrize(
    "post_rollback_stage_idx",
    range(len(post_rollback_stages)),
    ids=post_rollback_stages
)
def test_commands_SWUpdate_run_post_rollback_fail(
    patch_logging, mocker, mock_swupdate, post_rollback_stage_idx
):
    mock_manager, mocks, calls = mock_swupdate
    _idx = post_rollback_stage_idx
    stage = post_rollback_stages[_idx]
    stage_args = []
    parts = stage.split(':')
    if len(parts) > 1:
        stage = parts[0]
        stage_args = tuple(parts[1:])
    update_lower_exc = TypeError('some-error')
    post_rollback_exc = ValueError('some-post-rollback-error')
    target = 'some-target'

    # Note. just emulate sw update on early stage
    #       since it's not an object of testing here
    def apply_side_effect(component, *args, **kwargs):
        if component == 'provisioner':
            raise update_lower_exc
        else:
            return mocker.DEFAULT

    _curr_yum_rollback_side_effect = (
        mocks['YumRollbackManager'].return_value.__enter__.side_effect
    )

    def yum_rollback_side_effect(*args, **kwargs):
        def _side_effect(*args, **kwargs):
            if not stage_args or args == stage_args:
                raise post_rollback_exc
            else:
                return mocker.DEFAULT
        mocks[stage].side_effect = _side_effect
        return _curr_yum_rollback_side_effect(*args, **kwargs)

    mocks['_update_component'].side_effect = apply_side_effect
    mocks['YumRollbackManager'].return_value.__enter__.side_effect = (
        yum_rollback_side_effect
    )

    with pytest.raises(SWUpdateFatalError) as excinfo:
        commands.SWUpdate().run(target)

    exc = excinfo.value
    assert type(exc) is SWUpdateFatalError
    assert type(exc.reason) is SWStackUpdateError
    assert exc.reason.reason is update_lower_exc
    assert exc.rollback_error is post_rollback_exc

    expected_calls = [
        calls['ensure_cluster_is_healthy'](),
        calls['_ensure_update_repos_configuration'](target),
        calls['_consul_export']('update-pre'),
        calls['YumRollbackManager'](
            target,
            multiple_targets_ok=True,
            pre_rollback_cb=commands._pre_yum_rollback
        ),
        calls['YumRollbackManager']().__enter__(),
        calls['YumRollbackManager']()._resolve_last_txn_ids(),
        calls['cluster_maintenance_enable'](),
        calls['_update_component']("provisioner", target),
        calls['YumRollbackManager']().__exit__(
            SWStackUpdateError,
            # XXX semes not valuable to check exact exc and trace as well
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][1],
            mocks['YumRollbackManager'].return_value.__exit__.call_args[0][2]
        ),
        calls['YumRollbackManager']()._yum_rollback()
    ]

    for _stage in post_rollback_stages[:(_idx + 1)]:
        stage_args = []
        parts = _stage.split(':')
        if len(parts) > 1:
            _stage = parts[0]
            stage_args = parts[1:]
        elif _stage in (
            '_apply_provisioner_config',
            'apply_ha_post_update'
        ):
            stage_args = [target]

        expected_calls.append(calls[_stage](*stage_args))

    assert mock_manager.mock_calls == expected_calls


def test_commands_ConfigureCortx(monkeypatch):
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

    cmd = commands.ConfigureCortx()

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


# ### FWUpdate ###

@pytest.mark.integration1
def test_commands_FWUpdate_happy_path(
    mocker, tmpdir_function, storage_enclosure_data, fw_source,
    controller_cli_script, state_fun_executer_m
):
    ip, user, passwd = storage_enclosure_data

    commands.FWUpdate().run(fw_source)

    state_fun_executer_m.execute.assert_called_once_with(
        'cmd.run',
        fun_kwargs=dict(
            name=(
                f"{controller_cli_script} host -h {ip} "
                f"-u {user} -p {passwd} --update-fw {fw_source}"
            )
        )
    )


# ### RebootController ###

@pytest.mark.integration1
def test_commands_RebootController_happy_path(
    mocker, tmpdir_function, storage_enclosure_data,
    controller_cli_script, state_fun_executer_m
):
    ip, user, passwd = storage_enclosure_data
    target_ctrl = 'somectrl'

    commands.RebootController().run(target_ctrl)

    state_fun_executer_m.execute.assert_called_once_with(
        'cmd.run',
        fun_kwargs=dict(
            name=(
                f"{controller_cli_script} host -h {ip} "
                f"-u {user} -p {passwd} --restart-ctrl {target_ctrl}"
            )
        )
    )


# ### ShutdownController ###

@pytest.mark.integration1
def test_commands_ShutdownController_happy_path(
    mocker, tmpdir_function, storage_enclosure_data,
    controller_cli_script, state_fun_executer_m
):
    ip, user, passwd = storage_enclosure_data
    target_ctrl = 'somectrl'

    commands.ShutdownController().run(target_ctrl)

    state_fun_executer_m.execute.assert_called_once_with(
        'cmd.run',
        fun_kwargs=dict(
            name=(
                f"{controller_cli_script} host -h {ip} "
                f"-u {user} -p {passwd} --shutdown-ctrl {target_ctrl}"
            )
        )
    )
