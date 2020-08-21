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

from provisioner import __main__
from provisioner.commands import commands
from provisioner.config import (
    PRVSNR_CLI_OUTPUT,
    PRVSNR_CLI_MACHINE_OUTPUT,
    LOG_CONSOLE_HANDLER as console_handler,
    LOG_FILE_HANDLER as logfile_handler,
    LOG_FORCED_LOGFILE_CMDS,
    LOG_ROOT_DIR
)


@pytest.fixture
def set_logging_m(mocker, mock_manager):
    set_logging_m = mocker.patch.object(
        __main__.log, 'set_logging', autospec=True
    )
    mock_manager.attach_mock(set_logging_m.mock, 'set_logging')
    return set_logging_m


@pytest.fixture
def _set_logging_m(mocker, mock_manager):
    _set_logging_m = mocker.patch.object(
        __main__, '_set_logging', autospec=True
    )
    mock_manager.attach_mock(_set_logging_m.mock, '_set_logging')
    return _set_logging_m


@pytest.fixture
def output_res_m(mocker, mock_manager):
    output_res_m = mocker.patch.object(
        __main__, 'output_res', autospec=True
    )
    mock_manager.attach_mock(output_res_m.mock, 'output_res')
    return output_res_m


@pytest.fixture
def prepare_res_m(mocker, mock_manager):
    prepare_res_m = mocker.patch.object(
        __main__, 'prepare_res', autospec=True
    )
    mock_manager.attach_mock(prepare_res_m.mock, 'prepare_res')
    return prepare_res_m


@pytest.fixture
def _main_m(mocker, mock_manager):
    _main_m = mocker.patch.object(
        __main__, '_main', autospec=True
    )
    mock_manager.attach_mock(_main_m.mock, '_main')
    return _main_m


def test_main_generate_logfile_filename(mocker):
    cmd = 'somecommmand'
    ts = 'somets'
    pid = 123
    thread_id = 456

    datetime_m = mocker.patch.object(
        __main__, 'datetime', autospec=True
    )
    strftime_m = datetime_m.now.return_value.strftime
    strftime_m.return_value = ts

    mocker.patch.object(
        __main__.os, 'getpid', autospec=True, return_value=pid
    )
    mocker.patch.object(
        __main__.threading, 'get_ident', autospec=True, return_value=thread_id
    )

    generated = __main__._generate_logfile_filename(cmd)

    strftime_m.assert_called_once_with("%Y%m%dT%H:%M:%S")
    assert generated.parent == LOG_ROOT_DIR

    base, _ts, _pid, _thread_id, suffix = generated.name.split('.')
    assert base == cmd
    assert _ts == ts
    assert int(_pid) == pid
    assert int(_thread_id) == thread_id
    assert suffix == 'log'


@pytest.mark.parametrize("output_type", PRVSNR_CLI_OUTPUT)
def test_main_set_logging_no_console_for_machine_output(
    mocker, set_logging_m, log_args_builder, output_type
):
    logging = {
        'handlers': {
            console_handler: {
                'stream': 'ext://sys.stderr'
            }
        },
        'root': {
            'handlers': [console_handler],
        }
    }

    LogArgs = log_args_builder(logging)
    log_args = LogArgs()

    assert getattr(log_args, console_handler) is True

    __main__._set_logging(output_type, log_args)
    assert getattr(log_args, console_handler) is (
        output_type not in PRVSNR_CLI_MACHINE_OUTPUT
    )


@pytest.mark.parametrize("cmd", list(commands))
def test_main_set_logging_forced_logfile_for_cmds(
    mocker, set_logging_m, log_args_builder, cmd
):
    logging = {
        'handlers': {
            logfile_handler: {
                'filename': 'somefile',
                'maxBytes': 123,
                'backupCount': 456,
                'filters': ['cmd_filter']
            }
        },
        'filters': {
            'cmd_filter': {
                '()': 'provisioner.log.CommandFilter',
                'cmd': 'unknown'
            }
        },
        'root': {
            'handlers': [],
        }
    }

    LogArgs = log_args_builder(logging)
    log_args = LogArgs(cmd=cmd)

    assert getattr(log_args, logfile_handler) is False

    __main__._set_logging('plain', log_args)
    assert getattr(log_args, logfile_handler) is (
        cmd in LOG_FORCED_LOGFILE_CMDS
    )


def test_main_set_logging_logfile_filename(
    mocker, set_logging_m, log_args_builder
):
    filename = 'somefile'
    anotherfilename = 'somefile2'
    generated_filename = 'somegeneratedfilename'

    logging = {
        'handlers': {
            logfile_handler: {
                'filename': filename,
                'maxBytes': 123,
                'backupCount': 456,
                'filters': ['cmd_filter']
            }
        },
        'filters': {
            'cmd_filter': {
                '()': 'provisioner.log.CommandFilter',
                'cmd': 'unknown'
            }
        },
        'root': {
            'handlers': [logfile_handler],
        }
    }

    mocker.patch.object(
        __main__,
        '_generate_logfile_filename',
        autospec=True,
        return_value=generated_filename
    )

    LogArgs = log_args_builder(logging)

    # default case
    log_args = LogArgs(cmd=LOG_FORCED_LOGFILE_CMDS[0])

    log_config = log_args.config()['handlers'][logfile_handler]
    assert log_config['filename'] == filename

    __main__._set_logging('plain', log_args)

    log_config = log_args.config()['handlers'][logfile_handler]
    assert log_config['filename'] == generated_filename

    # custom case
    log_args = LogArgs(
        **({
            'cmd': LOG_FORCED_LOGFILE_CMDS[0],
            f'{logfile_handler}_filename': anotherfilename
        })
    )

    log_config = log_args.config()['handlers'][logfile_handler]
    assert log_config['filename'] == anotherfilename

    __main__._set_logging('plain', log_args)

    log_config = log_args.config()['handlers'][logfile_handler]
    assert log_config['filename'] == anotherfilename


@pytest.mark.patch_logging([(__main__, ('error',))])
@pytest.mark.parametrize("output_type", PRVSNR_CLI_OUTPUT)
def test_main_exc(
    mocker, mock_manager, _set_logging_m, output_res_m, prepare_res_m,
    output_type, patch_logging
):
    exc = ValueError('some error')

    # expecting set_logging to be at the beginning
    # of the main logic
    _set_logging_m.side_effect = exc

    # TODO DOC EXAMPLE how to patch variables
    mocker.patch(
        'provisioner.__main__.output_type', output_type
    )

    prepare_res_m.return_value = 'someres'

    with pytest.raises(SystemExit) as excinfo:
        __main__.main()

    assert excinfo.value.code == 1

    expected_calls = [
        mocker.call._set_logging(output_type)
    ]

    if output_type != 'plain':
        expected_calls.extend([
            mocker.call.prepare_res(output_type, ret='', exc=exc),
            mocker.call.output_res(output_type, 'someres')
        ])

    assert mock_manager.mock_calls == expected_calls


@pytest.mark.parametrize("output_type", PRVSNR_CLI_OUTPUT)
def test_main_happy_path(
    mocker, mock_manager, _set_logging_m, output_res_m, prepare_res_m, _main_m,
    output_type
):
    ret = {
        'some-key': 'some-value'
    }

    prepare_res_m.return_value = 'someres'

    mocker.patch(
        'provisioner.__main__.output_type', output_type
    )

    _main_m.return_value = ret

    __main__.main()

    expected_calls = [
        mocker.call._set_logging(output_type),
        mocker.call._main(),
    ]

    if output_type == 'plain':
        expected_calls.extend([
            mocker.call.output_res(output_type, ret)
        ])
    else:
        expected_calls.extend([
            mocker.call.prepare_res(output_type, ret=ret, exc=None),
            mocker.call.output_res(output_type, 'someres')
        ])

    assert mock_manager.mock_calls == expected_calls
