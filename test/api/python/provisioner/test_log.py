import pytest
import attr
from copy import deepcopy

from provisioner import (
    log, config, inputs
)

null_handler = config.LOG_NULL_HANDLER
console_handler = config.LOG_CONSOLE_HANDLER
logfile_handler = config.LOG_FILE_HANDLER
cmd_filter = config.LOG_CMD_FILTER


# TODO tests for commands and args


# HELPERS AND FIXTURES

def check_attr_in_cls(attr_name, cls, **fields):
    _attr = attr.fields_dict(cls)[attr_name]

    metadata = fields.pop('metadata', None)
    if metadata:
        assert len(_attr.metadata) == len(metadata)
        for k, v in metadata.items():
            assert _attr.metadata[k] == v
    else:
        assert not len(_attr.metadata)

    for k, v in fields.items():
        assert getattr(_attr, k) == v


@pytest.fixture
def reset_logging_m(mocker, mock_manager):
    reset_logging_m = mocker.patch.object(log, 'reset_logging', autospec=True)
    mock_manager.attach_mock(reset_logging_m.mock, 'reset_logging')
    return reset_logging_m


@pytest.fixture
def dictConfig_m(mocker, mock_manager):
    dictConfig_m = mocker.patch.object(
        log.logging.config, 'dictConfig', autospec=True
    )

    mock_manager.attach_mock(dictConfig_m.mock, 'dictConfig')
    return dictConfig_m


# TESTS

@pytest.mark.parametrize('cmd', [None, 'somecmd'])
def test_log_log_args_cmd(log_args_builder, cmd):
    handler = 'somehandler'
    logging = {
        'handlers': {
            handler: {}
        },
        'root': {
            'handlers': [handler],
        }
    }

    if cmd:
        for default in (None, 'somedefault'):
            logging['filters'] = {
                cmd_filter: {}
            }

            if default:
                logging['filters'][cmd_filter]['cmd'] = default

            LogArgs = log_args_builder(logging)

            check_attr_in_cls(
                'cmd', LogArgs,
                type=str,
                default=('unknown' if default is None else default)
            )
    else:
        LogArgs = log_args_builder(logging)
        assert 'cmd' not in attr.fields_dict(LogArgs)


@pytest.mark.parametrize('level', [None, 'somelevel'])
def test_log_log_args_level(log_args_builder, level):
    handler = 'somehandler'
    logging = {
        'handlers': {
            handler: {}
        },
        'root': {
            'handlers': [handler],
        }
    }
    if level:
        logging['handlers'][handler]['level'] = level

    LogArgs = log_args_builder(logging)

    if level:
        check_attr_in_cls(
            'somehandler_level', LogArgs,
            type=str,
            default=level,
            metadata={
                inputs.METADATA_ARGPARSER: {
                    'help': f"{handler} log level",
                    'choices': ['DEBUG', 'INFO', 'WARN', 'ERROR']
                }
            }
        )

        log_args = LogArgs(somehandler_level=level)
        assert hasattr(log_args.handlers[handler], 'level')
        assert log_args.handlers[handler].level == level
    else:
        assert 'somehandler_level' not in attr.fields_dict(LogArgs)


@pytest.mark.parametrize('formatter', [None, 'someformatter'])
def test_log_log_args_formatter(log_args_builder, formatter):
    handler = 'somehandler'
    logging = {
        'formatters': {
            'formatter1': {},
            'formatter2': {},
        },
        'handlers': {
            handler: {}
        },
        'root': {
            'handlers': [handler],
        }
    }
    if formatter:
        logging['handlers'][handler]['formatter'] = formatter

    LogArgs = log_args_builder(logging)
    if formatter:
        check_attr_in_cls(
            'somehandler_formatter', LogArgs,
            type=str,
            default=formatter,
            metadata={
                inputs.METADATA_ARGPARSER: {
                    'help': f"{handler} log records format",
                    'choices': list(logging['formatters'])
                }
            }
        )

        log_args = LogArgs(somehandler_formatter=formatter)
        assert hasattr(log_args.handlers[handler], 'formatter')
        assert log_args.handlers[handler].formatter == formatter
    else:
        assert 'somehandler_formatter' not in attr.fields_dict(LogArgs)


def test_log_log_args_no_formatters(log_args_builder):
    LogArgs = log_args_builder({
        'handlers': {
            'somehandler': {
                'class': 'logging.StreamHandler',
                'formatter': 'someformatter'
            }
        },
        'root': {
            'handlers': ['somehandler'],
        },
    })
    assert 'somehandler_formatter' not in attr.fields_dict(LogArgs)


def test_log_log_args_console_stream(log_args_builder):
    stream = 'somestream'
    logging = {
        'handlers': {
            console_handler: {
                'stream': f'ext://sys.{stream}'
            }
        },
        'root': {
            'handlers': [console_handler],
        }
    }

    LogArgs = log_args_builder(logging)

    check_attr_in_cls(
        'console_stream', LogArgs,
        type=str,
        default=stream[-6:],
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': f"{console_handler} log stream",
                'choices': ['stderr', 'stdout']
            }
        }
    )

    log_args = LogArgs(console_stream=stream)
    assert hasattr(log_args.handlers[console_handler], 'stream')
    assert log_args.handlers[console_handler].stream == f'ext://sys.{stream}'


def test_log_log_args_logfile_attrs(log_args_builder):
    filename = 'some/file/path'
    maxBytes = 123
    backupCount = 345

    logging = {
        'handlers': {
            logfile_handler: {
                'filename': filename,
                'maxBytes': maxBytes,
                'backupCount': backupCount
            }
        },
        'root': {
            'handlers': [logfile_handler],
        }
    }

    LogArgs = log_args_builder(logging)

    check_attr_in_cls(
        'logfile_filename', LogArgs,
        type=str,
        default=filename,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': f"{logfile_handler} handler file path",
                'metavar': 'FILE'
            }
        }
    )

    check_attr_in_cls(
        'logfile_maxBytes', LogArgs,
        type=int,
        default=maxBytes,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    f"{logfile_handler} handler "
                    "max file size in bytes"
                ),
                'metavar': 'BYTES',
                'type': int
            }
        }
    )

    check_attr_in_cls(
        'logfile_backupCount', LogArgs,
        type=int,
        default=backupCount,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    f"{logfile_handler} handler "
                    "max backup files number"
                ),
                'metavar': 'NUMBER',
                'type': int
            }
        }
    )

    log_args = LogArgs(
        logfile_filename=filename,
        logfile_maxBytes=maxBytes,
        logfile_backupCount=backupCount
    )
    assert hasattr(log_args.handlers[logfile_handler], 'filename')
    assert log_args.handlers[logfile_handler].filename == filename
    assert hasattr(log_args.handlers[logfile_handler], 'maxBytes')
    assert log_args.handlers[logfile_handler].maxBytes == maxBytes
    assert hasattr(log_args.handlers[logfile_handler], 'backupCount')
    assert log_args.handlers[logfile_handler].backupCount == backupCount


# TODO DOC pytest ids
@pytest.mark.parametrize('enabled', [True, False], ids=['enabled', 'disabled'])
def test_log_log_args_handler_switcher(log_args_builder, enabled):
    handler = 'somehandler'
    logging = {
        'handlers': {
            handler: {}
        },
        'root': {
            'handlers': [handler] if enabled else [],
        }
    }

    LogArgs = log_args_builder(logging)
    check_attr_in_cls(
        handler, LogArgs,
        type=bool,
        default=enabled,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': f"{handler} logging handler",
                'action': 'store_bool'
            }
        }
    )


@pytest.mark.parametrize('enabled', [True, False], ids=['enabled', 'disabled'])
def test_log_log_args_null_handler(log_args_builder, enabled):
    logging = {
        'handlers': {
            null_handler: {}
        },
        'root': {
            'handlers': [null_handler] if enabled else [],
        }
    }

    LogArgs = log_args_builder(logging)
    check_attr_in_cls(
        null_handler, LogArgs,
        init=False,
        type=bool,
        default=enabled,
        metadata=None
    )


def test_log_log_args_config(log_args_builder):
    handler = 'somehandler'
    console_handler = config.LOG_CONSOLE_HANDLER
    level = 'somelevel'
    formatter = 'someformatter'
    stream = 'somestream'
    cmd = 'somecommand'

    logging = {
        'formatters': {
            formatter: {}
        },
        'filters': {
            cmd_filter: {}
        },
        'handlers': {
            handler: {
                'level': '123',
                'formatter': '456'
            },
            console_handler: {
                'level': '789',
                'formatter': '987',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'handlers': [handler, console_handler],
        }
    }
    original_config = deepcopy(logging)

    LogArgs = log_args_builder(logging)

    # default
    logging['filters'][cmd_filter]['cmd'] = 'unknown'

    log_args = LogArgs()
    assert LogArgs.original_config() == original_config
    assert log_args.config() == logging

    # cmd is None
    log_args = LogArgs(cmd=None)
    assert LogArgs.original_config() == original_config
    assert log_args.config() == logging

    # other args
    log_args = {
        'cmd': cmd,
        f'{handler}': False,
        f'{handler}_level': level,
        f'{handler}_formatter': formatter,
        f'{console_handler}': True,
        f'{console_handler}_level': level,
        f'{console_handler}_formatter': formatter,
        f'{console_handler}_stream': stream
    }

    logging['filters'][cmd_filter]['cmd'] = cmd
    logging['handlers'][console_handler]['level'] = level
    logging['handlers'][console_handler]['formatter'] = formatter
    logging['root']['handlers'] = [console_handler]
    logging['handlers'][console_handler]['stream'] = f'ext://sys.{stream}'

    log_args = LogArgs(**log_args)
    assert log_args.config() == logging


@pytest.mark.parametrize(
    'cmd', [None, 'somecmd'], ids=['nocmd', 'somecmd']
)
@pytest.mark.parametrize(
    'log_args', [None, 1], ids=['nologargs', 'somelogargs']
)
def test_log_set_logging(
    mocker, mock_manager, reset_logging_m, dictConfig_m,
    log_args_builder, cmd, log_args
):
    LogArgs = None
    if log_args:
        logging = {
            'filters': {
                'some_filter': {},
                cmd_filter: {},
            },
            'handlers': {
                'handler1': {},
                'handler2': {}
            },
            'root': {
                'handlers': ['handler1'],
            }
        }
        LogArgs = log_args_builder(logging)
        log_args = LogArgs(cmd=cmd)

    log_config = (
        log.prvsnr_config.logging if log_args is None
        else log_args.config()
    )
    log.set_logging(log_args=log_args)

    assert mock_manager.mock_calls == [
        mocker.call.reset_logging(),
        mocker.call.dictConfig(log_config)
    ]
