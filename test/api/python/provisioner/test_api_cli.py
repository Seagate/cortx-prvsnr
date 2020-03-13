import pytest
import subprocess
from typing import Any, Callable
import attr
import json

from provisioner import _api_cli as api
from provisioner.__main__ import _prepare_res, _prepare_output
from provisioner.errors import ProvisionerError, SaltError


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


def test_api_cli_run_cmd_subprocess_run_fails_unexpectedly(subprocess_runner):
    cmd_name = 'some-command'
    exc_args = ('some-error',)
    exc = ValueError(*exc_args)

    subprocess_runner.res = exc

    with pytest.raises(ProvisionerError) as excinfo:
        api._run_cmd([cmd_name])

    assert excinfo.value.args == (repr(exc),)


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
            lambda cli_exc: ('some-stderr-1',),
            stdout='',
            stderr='some-stderr-1'
        ),
        CliFailScenario(
            SaltError,
            ProvisionerError,
            lambda cli_exc: ('some-stderr-2',),
            stdout=_prepare_output('json', {}),
            stderr='some-stderr-2'
        ),
        CliFailScenario(
            SaltError,
            ProvisionerError,
            lambda cli_exc: ('some-stderr-3',),
            stdout=_prepare_output('json', {'ret': '123'}),
            stderr='some-stderr-3'
        ),
        CliFailScenario(
            SaltError,
            SaltError
        )
    ],
    ids=[
        'unexpected_output_empty_str',
        'unexpected_output_empty_dict',
        'unexpected_output_no_exc',
        'expected'
    ]
)
def test_api_cli_run_cmd_cli_fails(subprocess_runner, fail_scenario):
    exc_args = ('some-error',)
    exc = fail_scenario.cli_exc_type(*exc_args)

    subprocess_exc = subprocess.CalledProcessError(
        1, 'some-command',
        output=(
            fail_scenario.stdout if fail_scenario.stdout is not None
            else _prepare_output('json', _prepare_res('json', exc=exc))
        ),
        stderr=fail_scenario.stderr
    )

    subprocess_runner.res = subprocess_exc

    with pytest.raises(fail_scenario.expected_exc_type) as excinfo:
        api._run_cmd([subprocess_exc.cmd])

    assert excinfo.value.args == fail_scenario.expected_exc_args_cb(exc)

    # check 'raise ... from' expression is used
    assert excinfo.value.__cause__ is subprocess_runner.res


def test_api_cli_run_cmd_cli_succedes(subprocess_runner):
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
            'json', _prepare_res('json', ret=ret)
        )
    )
    assert api._run_cmd([cmd_name]) == ret
