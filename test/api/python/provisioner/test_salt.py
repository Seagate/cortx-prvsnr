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

import pytest
import functools

from provisioner import salt
from provisioner.errors import (
    SaltCmdRunError, SaltNoReturnError, SaltCmdResultError,
    ProvisionerError
)
from provisioner.config import LOCAL_MINION
from provisioner import UNCHANGED, MISSED


def generate_salt_client_mock(cmd_f, cmd_async_f=None):
    class SomeClient:
        def cmd(self, *args, **kwargs):
            return cmd_f(*args, **kwargs)

        def cmd_sync(self, *args, **kwargs):
            return cmd_f(*args, **kwargs)

        def cmd_async(self, *args, **kwargs):
            return cmd_async_f(*args, **kwargs)
    return SomeClient


@pytest.fixture(autouse=True)
def local_minion_id(monkeypatch):
    local_minion_id = 'some_local_minion_id'
    monkeypatch.setattr(
        salt, 'local_minion_id', lambda: local_minion_id
    )
    return local_minion_id


# TODO DOC
@pytest.fixture(autouse=True)
def patch_logging(request):
    request.applymarker(pytest.mark.patch_logging(
        [(salt, ('error', 'warning', 'info'))]
    ))
    request.getfixturevalue('patch_logging')


@pytest.mark.parametrize("eauth", [True, False], ids=['eauth', 'root'])
def test_salt_runner_cmd(monkeypatch, eauth):
    salt_cmd_args = []
    salt_cmd_res = {}
    exc = None

    def cmd(*args, **kwargs):
        nonlocal salt_cmd_args
        if exc:
            raise exc
        salt_cmd_args.append(
            (args, kwargs)
        )
        return salt_cmd_res

    monkeypatch.setattr(
        salt, 'salt_runner_client',
        lambda: generate_salt_client_mock(
            cmd, functools.partial(cmd, _async=True)
        )()
    )

    # TEST ARGS PASSED
    fun = 'some_fun'
    fun_args = None
    fun_kwargs = dict(fun_kwargs1=1, fun_kwargs2=2)
    nowait = False
    kwargs = dict(some_key1=3, some_key2=4)
    if eauth:
        kwargs.update(dict(username='user', password='passwd', eauth='pam'))
    salt_cmd_base_result = {
        'jid': '12345',
        '_stamp': 'some-timestamp',
        'fun': 'some.fun',
        'user': 'some-user',
        'success': True,
        'return': 'some-return'
    }
    if eauth:
        salt_cmd_good_res = {
            'data': salt_cmd_base_result
        }
    else:
        salt_cmd_good_res = salt_cmd_base_result

    salt_cmd_res = salt_cmd_good_res

    def _call():
        nonlocal salt_cmd_args
        salt_cmd_args = []
        return salt._salt_runner_cmd(
            fun, fun_args, fun_kwargs,
            nowait=nowait, **kwargs
        )

    def _check_exc_attrs(exc, _locals):
        _kwargs = dict(_locals['kwargs'])
        if not eauth:
            _kwargs['print_event'] = False
            _kwargs['full_return'] = True

        for attr in (
            'fun', 'fun_args', 'fun_kwargs', 'nowait'
        ):
            assert getattr(exc.cmd_args, attr) == _locals[attr]
        assert exc.cmd_args.kw == _kwargs

    salt_cmd_args = []
    _call()
    if eauth:
        assert salt_cmd_args == [
            (
                (
                    dict(
                        fun=fun,
                        arg=(), kwarg=fun_kwargs,
                        **kwargs
                    ),
                ),
                dict(
                    full_return=True
                )
            )
        ]
    else:
        assert salt_cmd_args == [
            (
                (fun,),
                dict(
                    arg=(), kwarg=fun_kwargs,
                    full_return=True, print_event=False,
                    **kwargs
                )
            )
        ]

    salt_cmd_args = []
    fun_args = ('fun_args1', 'fun_args2')
    _call()
    if eauth:
        assert salt_cmd_args == [
            (
                (
                    dict(
                        fun=fun,
                        arg=fun_args, kwarg=fun_kwargs,
                        **kwargs
                    ),
                ),
                dict(
                    full_return=True
                ),
            )
        ]
    else:
        assert salt_cmd_args == [
            (
                (fun,),
                dict(
                    arg=fun_args, kwarg=fun_kwargs,
                    full_return=True, print_event=False,
                    **kwargs
                )
            )
        ]

    nowait = True
    salt_cmd_args = []
    with pytest.raises(NotImplementedError):
        _call()
    nowait = False

    # TEST ERRORS RAISED
    #   some exception during run
    exc = ValueError('some error')
    with pytest.raises(SaltCmdRunError) as excinfo:
        _call()
    assert excinfo.value.reason is exc
    _check_exc_attrs(excinfo.value, locals())
    exc = None

    #   falsy res
    for salt_cmd_res in (0, {}, [], False):
        with pytest.raises(SaltNoReturnError) as excinfo:
            _call()
        assert (
                excinfo.value.reason == (
                    'Empty salt result: {}'
                    .format(salt_cmd_res)
                )
        )
        _check_exc_attrs(excinfo.value, locals())

    #   non-dict results
    salt_cmd_res = [1, 2, 3]
    with pytest.raises(SaltCmdRunError) as excinfo:
        _call()
    assert (
        excinfo.value.reason == (
            'RunnerClient result type is not a dictionary: {}'
            .format(type(salt_cmd_res))
        )
    )
    _check_exc_attrs(excinfo.value, locals())

    #   unexpected result format - no data field at top (eauth only)
    if eauth:
        salt_cmd_res = {'some-key': 'some-value'}
        with pytest.raises(SaltCmdRunError) as excinfo:
            _call()
        assert (
            excinfo.value.reason == (
                'no data key in RunnerClient result dictionary: {}'
                .format(salt_cmd_res)
            )
        )
        _check_exc_attrs(excinfo.value, locals())

    #   unexpected result format - missed expected fields
    salt_cmd_res = {'some-key': 'some-value'}
    if eauth:
        salt_cmd_res = {'data': salt_cmd_res}
    with pytest.raises(SaltCmdRunError) as excinfo:
        _call()
    assert (
        excinfo.value.reason == (
            'Failed to parse salt runner result: {}'
            .format(salt_cmd_res)
        )
    )
    _check_exc_attrs(excinfo.value, locals())

    #    raise on fail
    salt_cmd_res = salt_cmd_good_res
    if eauth:
        salt_cmd_res['data']['success'] = False
    else:
        salt_cmd_res['success'] = False
    with pytest.raises(SaltCmdResultError) as excinfo:
        _call()
    if eauth:
        assert (
            excinfo.value.reason == salt_cmd_res['data']['return']
        )
    else:
        assert (
            excinfo.value.reason == salt_cmd_res['return']
        )
    _check_exc_attrs(excinfo.value, locals())


def test_salt_client_cmd(monkeypatch):
    salt_cmd_args = []
    salt_cmd_res = {}
    exc = None

    def cmd(*args, **kwargs):
        nonlocal salt_cmd_args
        if exc:
            raise exc
        salt_cmd_args.append(
            (args, kwargs)
        )
        return salt_cmd_res

    monkeypatch.setattr(
        salt, 'salt_local_client',
        lambda: generate_salt_client_mock(
            cmd, functools.partial(cmd, _async=True)
        )()
    )

    # TEST ARGS PASSED
    targets = 'some-targets'
    fun = 'some_fun'
    fun_args = None
    fun_kwargs = dict(fun_kwargs1=1, fun_kwargs2=2)
    nowait = False
    kwargs = dict(some_key1=3, some_key2=4)
    salt_cmd_res = {'some-node': 'some-res'}

    def _call():
        nonlocal salt_cmd_args
        salt_cmd_args = []
        return salt._salt_client_cmd(
            targets, fun, fun_args, fun_kwargs,
            nowait=nowait, **kwargs
        )

    def _check_exc_attrs(exc, _locals):
        _kwargs = dict(_locals['kwargs'])
        _kwargs['full_return'] = True

        for attr in (
            'targets', 'fun', 'fun_args', 'fun_kwargs', 'nowait'
        ):
            assert getattr(exc.cmd_args, attr) == _locals[attr]
        assert exc.cmd_args.kw == _kwargs

    salt_cmd_args = []
    _call()
    assert salt_cmd_args == [
        (
            (targets, fun),
            dict(arg=(), kwarg=fun_kwargs, full_return=True, **kwargs)
        )
    ]

    salt_cmd_args = []
    fun_args = ('fun_args1', 'fun_args2')
    _call()
    assert salt_cmd_args == [
        (
            (targets, fun),
            dict(arg=fun_args, kwarg=fun_kwargs, full_return=True, **kwargs)
        )
    ]

    nowait = True
    salt_cmd_args = []
    salt_cmd_res = {'some-node': 'some-res'}
    _call()
    assert salt_cmd_args == [
        (
            (targets, fun),
            dict(
                arg=fun_args, kwarg=fun_kwargs,
                full_return=True, _async=True, **kwargs
            )
        )
    ]

    # TEST ERRORS RAISED
    #   some exception during run
    exc = ValueError('some error')
    with pytest.raises(SaltCmdRunError) as excinfo:
        _call()
    assert excinfo.value.reason is exc
    _check_exc_attrs(excinfo.value, locals())
    exc = None

    #   falsy res for async run
    for nowait in (True, False):
        for salt_cmd_res in (0, {}, [], False):
            with pytest.raises(SaltNoReturnError) as excinfo:
                _call()
            assert (
                    excinfo.value.reason == (
                        'Async API returned empty result: {}'
                        .format(salt_cmd_res)
                    ) if nowait else (
                        'Empty salt result: {}'
                        .format(salt_cmd_res)
                    )
            )
            _check_exc_attrs(excinfo.value, locals())

    #   return with errors
    nowait = False
    salt_cmd_res = {
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
    #       non-state function
    fun = 'somefun'
    with pytest.raises(SaltCmdResultError) as excinfo:
        _call()
    assert excinfo.value.reason == {
        'some-node-id': salt_cmd_res['some-node-id']['ret']
    }
    _check_exc_attrs(excinfo.value, locals())

    #       state function
    fun = 'state.something'
    with pytest.raises(SaltCmdResultError) as excinfo:
        _call()
    _fails = {
        'some-node-id': {
            'some-task-id': {
                'comment': 'some comment',
                'changes': None
            }
        }
    }
    assert excinfo.value.reason == _fails
    _check_exc_attrs(excinfo.value, locals())

    # test return
    #   async result
    nowait = True
    salt_cmd_res = 'some-result'
    res = _call()
    assert res == salt_cmd_res
    nowait = False

    #   non dict salt result
    for val in ('some-result', ['some-result']):
        salt_cmd_res = val
        res = _call()
        assert res == salt_cmd_res

    #   result for a minion has 'ret' key
    salt_cmd_res = {
        'some-node-id': {
            'ret': {
                'some-task-id': {
                    'result': False,
                    'comment': 'some comment'
                }
            },
            'retcode': 0
        }
    }
    res = _call()
    assert res == {
        'some-node-id': salt_cmd_res['some-node-id']['ret']
    }

    #   result for a minion doesn't have 'ret' key
    salt_cmd_res = {
        'some-node-id': {
            'some-result'
        }
    }
    res = _call()
    assert res == salt_cmd_res

    #   a combination of two previous
    salt_cmd_res = {
        'some-node-id1': {
            'ret': {
                'some-task-id': {
                    'result': False,
                    'comment': 'some comment'
                }
            },
            'retcode': 0
        },
        'some-node-id2': {
            'some-result'
        }
    }
    res = _call()
    assert res == {
        'some-node-id1': salt_cmd_res['some-node-id1']['ret'],
        'some-node-id2': salt_cmd_res['some-node-id2'],
    }

    #   the same case but 'return' instead of 'ret'
    salt_cmd_res = {
        'some-node-id1': {
            'return': {
                'some-task-id': {
                    'result': False,
                    'comment': 'some comment'
                }
            },
            'retcode': 0
        },
        'some-node-id2': {
            'some-result'
        }
    }
    res = _call()
    assert res == {
        'some-node-id1': salt_cmd_res['some-node-id1']['return'],
        'some-node-id2': salt_cmd_res['some-node-id2'],
    }


def test_salt_function_run(monkeypatch, local_minion_id):
    _salt_client_cmd_args = []

    def _salt_client_cmd(*args, **kwargs):
        nonlocal _salt_client_cmd_args
        _salt_client_cmd_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        salt, '_salt_client_cmd', _salt_client_cmd
    )

    fun = 'some_state_fun1'
    fun_args = ('fun_args1', 'fun_args2')
    fun_kwargs = dict(fun_kwargs1=1, fun_kwargs2=2)
    kwargs = dict(some_key1=3, some_key2=4)

    _salt_client_cmd_args = []
    targets = 'some-targets'
    salt.function_run(
        fun,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        targets=targets,
        **kwargs
    )
    assert _salt_client_cmd_args == [
        (
            (targets, fun),
            dict(
                fun_args=fun_args,
                fun_kwargs=fun_kwargs,
                **kwargs
            )
        )
    ]

    _salt_client_cmd_args = []
    targets = LOCAL_MINION
    salt.function_run(
        fun,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        targets=targets,
        **kwargs
    )
    assert _salt_client_cmd_args == [
        (
            (local_minion_id, fun),
            dict(
                fun_args=fun_args,
                fun_kwargs=fun_kwargs,
                **kwargs
            )
        )
    ]


def test_salt_pillar_get(monkeypatch):
    function_run_args = []

    def function_run(*args, **kwargs):
        nonlocal function_run_args
        function_run_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        salt, 'function_run', function_run
    )

    targets = 'some-targets'

    function_run_args = []
    salt.pillar_get(
        targets=targets
    )
    assert function_run_args == [
        (
            ('pillar.items',),
            dict(
                targets=targets
            )
        )
    ]


def test_salt_pillar_refresh(monkeypatch):
    function_run_args = []

    def function_run(*args, **kwargs):
        nonlocal function_run_args
        function_run_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        salt, 'function_run', function_run
    )

    targets = 'some-targets'

    function_run_args = []
    salt.pillar_refresh(
        targets=targets
    )
    assert function_run_args == [
        (
            ('saltutil.refresh_pillar',),
            dict(
                targets=targets
            )
        )
    ]


def test_salt_cmd_run(monkeypatch):
    function_run_args = []

    def function_run(*args, **kwargs):
        nonlocal function_run_args
        function_run_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        salt, 'function_run', function_run
    )

    targets = 'some-targets'
    cmd = 'some_command'

    function_run_args = []
    salt.cmd_run(
        cmd,
        targets=targets,
    )
    assert function_run_args == [
        (
            ('cmd.run',),
            dict(
                fun_args=[cmd],
                targets=targets,
                fun_kwargs=dict(bg=False),
                **dict(timeout=None)
            )
        )
    ]


def test_salt_process_provisioner_cmd_res(monkeypatch, local_minion_id):
    monkeypatch.setattr(
        salt, 'process_cli_result', lambda res: res
    )

    res = 'some-res'
    with pytest.raises(ProvisionerError) as excinfo:
        salt.process_provisioner_cmd_res(res)
    assert str(excinfo.value) == (
        'Expected a dictionary of len = 1, provided: {}, {}'
        .format(type(res), res)
    )

    res = {'some-key': 'some-res'}
    ret = salt.process_provisioner_cmd_res(res)
    assert ret == 'some-res'

    res = {local_minion_id: 'some-result'}
    ret = salt.process_provisioner_cmd_res(res)
    assert ret == 'some-result'


def test_salt_provisioner_cmd(monkeypatch, local_minion_id):
    function_run_args = []
    function_run_res = {}

    def function_run(*args, **kwargs):
        nonlocal function_run_args
        function_run_args.append(
            (args, kwargs)
        )
        if isinstance(function_run_res, Exception):
            raise function_run_res
        else:
            return function_run_res

    monkeypatch.setattr(
        salt, 'function_run', function_run
    )

    monkeypatch.setattr(
        salt, 'process_provisioner_cmd_res',
        lambda res: res
    )

    # arguments passed to function_run
    cmd = 'some_command'
    fun_args = ('fun_args1', 'fun_args2', UNCHANGED)
    fun_kwargs = dict(fun_kwargs1=1, fun_kwargs2=MISSED)
    kwargs = dict(some_key1=3, some_key2=4)

    #   default fun_args and fun_kwargs
    function_run_args = []
    salt.provisioner_cmd(
        cmd,
        **kwargs
    )
    assert function_run_args == [
        (
            ('provisioner.{}'.format(cmd),),
            dict(
                fun_args=None,
                fun_kwargs=None,
                targets=local_minion_id,
                nowait=False,
                **kwargs
            )
        )
    ]

    #   some more complex case
    function_run_args = []
    salt.provisioner_cmd(
        cmd,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        **kwargs
    )
    assert function_run_args == [
        (
            ('provisioner.{}'.format(cmd),),
            dict(
                fun_args=['fun_args1', 'fun_args2', 'PRVSNR_UNCHANGED'],
                fun_kwargs=dict(fun_kwargs1=1, fun_kwargs2='PRVSNR_MISSED'),
                targets=local_minion_id,
                nowait=False,
                **kwargs
            )
        )
    ]

    # results with errors
    function_run_res = SaltCmdResultError(
        'some-cmd-args', {local_minion_id: 'some-res'}
    )
    #   sync
    assert salt.provisioner_cmd(
        cmd,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        **kwargs
    ) == function_run_res.reason

    #   async
    with pytest.raises(ProvisionerError) as excinfo:
        salt.provisioner_cmd(
            cmd,
            fun_args=fun_args,
            fun_kwargs=fun_kwargs,
            nowait=True,
            **kwargs
        )
    assert str(excinfo.value) == (
        'SaltCmdResultError is unexpected here: {!r}'.format(function_run_res)
    )

    # results no errors
    #   sync
    function_run_res = {local_minion_id: 'some-res'}
    assert salt.provisioner_cmd(
        cmd,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        **kwargs
    ) == function_run_res

    #   async
    function_run_res = {local_minion_id: 'some-res'}
    assert salt.provisioner_cmd(
        cmd,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        nowait=True,
        **kwargs
    ) == function_run_res


# TODO
#   - split into separate tests
#   - add tests for Caller (targets=LOCAL_MINION)
def test_salt_states_apply(monkeypatch):
    function_run_args = []

    def function_run(*args, **kwargs):
        nonlocal function_run_args
        function_run_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        salt, 'function_run', function_run
    )

    targets = 'some-targets'
    states = ['state1', 'state2', 'state3']

    function_run_args = []
    salt.states_apply(states, targets=targets)
    assert function_run_args == [
        (
            ('state.apply',),
            dict(
                fun_args=[state],
                targets=targets,
            )
        ) for state in states
    ]


def test_salt_state_fun_execute(monkeypatch):
    function_run_args = []

    def function_run(*args, **kwargs):
        nonlocal function_run_args
        function_run_args.append(
            (args, kwargs)
        )

    monkeypatch.setattr(
        salt, 'function_run', function_run
    )

    targets = 'some-targets'
    state_fun = 'some_state_fun1'
    fun_args = ('fun_args1', 'fun_args2')
    fun_kwargs = dict(fun_kwargs1=1, fun_kwargs2=2)
    kwargs = dict(some_key1=3, some_key2=4)

    function_run_args = []
    salt.state_fun_execute(
        state_fun,
        fun_args=fun_args,
        fun_kwargs=fun_kwargs,
        targets=targets,
        **kwargs
    )
    assert function_run_args == [
        (
            ('state.single',),
            dict(
                fun_args=([state_fun] + list(fun_args)),
                fun_kwargs=fun_kwargs,
                targets=targets,
                **dict(nowait=False, **kwargs)
            )
        )
    ]
