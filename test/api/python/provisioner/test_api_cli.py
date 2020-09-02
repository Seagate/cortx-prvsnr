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
import subprocess
from typing import Any, Callable
import json
import os

from provisioner.vendor import attr
from provisioner import _api_cli as api
from provisioner.__main__ import prepare_res, _prepare_output
from provisioner.errors import ProvisionerError, SaltError
from provisioner import NONE


@attr.s(auto_attribs=True)
class SubprocessRunner:
    res: Any = None

    def __call__(self, *args, **kwargs):
        if isinstance(self.res, Exception):
            raise self.res
        else:
            return self.res


@pytest.fixture
def subprocess_runner(monkeypatch):
    _subprocess_runner = SubprocessRunner()
    monkeypatch.setattr(subprocess, 'run', _subprocess_runner)
    return _subprocess_runner


# TODO IMPROVE split
@pytest.mark.patch_logging([(api, ('debug',))])
def test_api_cli_api_args_to_cli(patch_logging):
    fun = 'some-fun'
    # positional
    assert api.api_args_to_cli(
        fun, 'arg1', 'arg2', [1, 2, 3], {'4': {'5': 6}}
    ) == [
        fun, 'arg1', 'arg2', '[1, 2, 3]', '{"4": {"5": 6}}'
    ]
    # optional basic
    assert api.api_args_to_cli(fun, arg1=123) == [fun, '--arg1', '123']
    # optional '-' and '_'
    assert api.api_args_to_cli(fun, some_arg1=123) == [
        fun, '--some-arg1', '123'
    ]
    # optional True bool
    assert api.api_args_to_cli(fun, arg1=True) == [fun, '--arg1']
    # optional True bool
    assert api.api_args_to_cli(fun, arg1=False) == [fun]
    # optional None
    assert api.api_args_to_cli(fun, arg1=None) == [fun, '--arg1', str(NONE)]
    # optional List
    assert api.api_args_to_cli(
        fun, arg1=[1, 2, '3']
    ) == [fun, '--arg1', '[1, 2, "3"]']
    # optional Dict
    assert api.api_args_to_cli(
        fun, arg1={'1': {'2': 3, '4': '5'}}
    ) == [fun, '--arg1', '{"1": {"2": 3, "4": "5"}}']


@pytest.mark.patch_logging([(api, ('error',))])
def test_api_cli_run_cmd_subprocess_run_fails_unexpectedly(
    subprocess_runner, patch_logging
):
    cmd_name = 'some-command'
    exc_args = ('some-error',)
    exc = ValueError(*exc_args)

    subprocess_runner.res = exc

    with pytest.raises(ProvisionerError) as excinfo:
        api._run_cmd([cmd_name])

    assert excinfo.value.args == (repr(exc),)

    # check 'raise ... from' expression is used
    assert excinfo.value.__cause__ is subprocess_runner.res


@attr.s(auto_attribs=True)
class CliFailScenario:
    cli_exc_type: Exception
    expected_exc_type: Exception
    expected_exc_args_cb: Callable = lambda cli_exc: cli_exc.args
    stdout: str = None
    stderr: str = None


@pytest.mark.parametrize(
    "fail_scenario",
    [
        CliFailScenario(
            SaltError,
            ProvisionerError,
            lambda cli_exc: (
                "No return data found in '', stderr: 'some-stderr-1'",
            ),
            stdout='',
            stderr='some-stderr-1'
        ),
        CliFailScenario(
            SaltError,
            ProvisionerError,
            lambda cli_exc: (
                "No return data found in '{}', stderr: 'some-stderr-2'",
            ),
            stdout=_prepare_output('json', {}),
            stderr='some-stderr-2'
        ),
        CliFailScenario(
            SaltError,
            SaltError
        )
    ],
    ids=[
        'unexpected_output_empty_str',
        'unexpected_output_empty_dict',
        'expected'
    ]
)
@pytest.mark.patch_logging([(api, ('error',))])
def test_api_cli_run_cmd_cli_fails(
    subprocess_runner, fail_scenario, patch_logging
):
    exc_args = ('some-error',)
    exc = fail_scenario.cli_exc_type(*exc_args)

    subprocess_exc = subprocess.CalledProcessError(
        1, 'some-command',
        output=(
            fail_scenario.stdout if fail_scenario.stdout is not None
            else _prepare_output('json', prepare_res('json', exc=exc))
        ),
        stderr=fail_scenario.stderr
    )

    subprocess_runner.res = subprocess_exc

    with pytest.raises(fail_scenario.expected_exc_type) as excinfo:
        api._run_cmd([subprocess_exc.cmd])

    assert excinfo.value.args == fail_scenario.expected_exc_args_cb(exc)


@pytest.mark.patch_logging([(api, ('error',))])
def test_api_cli_run_cmd_cli_succedes(subprocess_runner, patch_logging):
    cmd_name = 'some-command'
    ret = {
        'some-key1': 'some-value1',
        'some-key2': ['some-value2'],
        'some-key3': {
            'some-key4': 'some-value4'
        },
    }

    # unexpected return format
    subprocess_runner.res = subprocess.CompletedProcess(
        [cmd_name], 0, stdout=json.dumps(ret, sort_keys=True, indent=4)
    )

    with pytest.raises(ProvisionerError) as excinfo:
        api._run_cmd([cmd_name])

    assert 'No return data found' in str(excinfo.value)

    # happy path
    subprocess_runner.res = subprocess.CompletedProcess(
        [cmd_name], 0, stdout=_prepare_output(
            'json', prepare_res('json', ret=ret)
        )
    )
    assert api._run_cmd([cmd_name]) == ret


@pytest.mark.patch_logging([(api, ('error',))])
def test_api_cli_set_env(mocker, patch_logging):
    cmd_name = 'some-command'
    env = {'SOMEENV': 'somevalue'}
    expected = os.environ.copy()
    expected.update(env)

    run_m = mocker.patch.object(api.subprocess, 'run', autospec=True)
    mocker.patch.object(
        api, 'process_cli_result', autospec=True
    )

    api._run_cmd([cmd_name], env=env)
    run_m.assert_called_once_with([cmd_name], env=expected)
