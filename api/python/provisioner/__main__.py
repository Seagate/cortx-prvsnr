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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import fileinput
import sys
import logging
import yaml
import threading
from datetime import datetime
from typing import Union, Any

from .vendor import attr
from . import (
    __version__,
    config,
    auth_init,
    serialize,
    _api,
    runner,
    log
)
from .commands import commands
from .base import prvsnr_config

from . import cli_parser

logger = logging.getLogger(__name__)

output_type = prvsnr_config.env['PRVSNR_OUTPUT']
log_args = None

GeneralArgs = attr.make_class("GeneralArgs", ('version',))
AuthArgs = attr.make_class("AuthArgs", ('username', 'password', 'eauth'))


def prepare_res(output_type, ret=None, exc=None):
    return {
        'ret': ret
    } if exc is None else {
        'exc': {
            'type': type(exc).__name__,
            'args': list(exc.args)
        }
    } if output_type == 'yaml' else {
        'exc': exc
    }


# TODO TEST
def _prepare_output(output_type, res):
    if output_type == 'plain':  # plain
        return str(res)
    elif output_type == 'yaml':
        return yaml.dump(res, default_flow_style=False, canonical=False)
    elif output_type == 'json':
        return serialize.dumps(res, sort_keys=True, indent=4)
    else:
        logger.error(
            "Unexpected output type {}".format(output_type)
        )
        raise ValueError('Unexpected output type {}'.format(output_type))


def output_res(output_type, res):
    data = _prepare_output(output_type, res)
    logger.debug("CLI output: {}".format(data))
    print(data)


# TODO TEST
# TODO TYPE for cmd Any
def _run_cmd(cmd: Union[str, Any], *args, **kwargs):
    logger.debug("Executing {}..".format(cmd))
    if type(cmd) is str:
        return _api.run(cmd, *args, **kwargs)
    else:
        return cmd.run(*args, **kwargs)


def _generate_logfile_filename(cmd):
    ts = datetime.now().strftime("%Y%m%dT%H:%M:%S")
    threadid = threading.get_ident()
    pid = os.getpid()
    return (config.LOG_ROOT_DIR / f'{cmd}.{ts}.{pid}.{threadid}.log')


def _set_logging(output_type, log_args=None):
    if log_args is None:
        log_args = log.LogArgs()

    # forcing some log settings based on output type
    #   disable console log handler for machine readable output
    if output_type in config.PRVSNR_CLI_MACHINE_OUTPUT:
        if hasattr(log_args, config.LOG_CONSOLE_HANDLER):
            setattr(log_args, config.LOG_CONSOLE_HANDLER, False)

    # forcibly enable and configure rotation file logging
    # for most important commands
    if getattr(log_args, 'cmd', None) in config.LOG_FORCED_LOGFILE_CMDS:
        if hasattr(log_args, config.LOG_FILE_HANDLER):
            # enable
            setattr(log_args, config.LOG_FILE_HANDLER, True)
            # set file to log if default value is set
            filename_attr = f'{config.LOG_FILE_HANDLER}_filename'
            if (
                getattr(log_args, filename_attr) ==
                attr.fields_dict(type(log_args))[filename_attr].default
            ):
                filename = _generate_logfile_filename(log_args.cmd)
                setattr(log_args, filename_attr, str(filename))
            log_args.update_handlers()

    # TODO IMPROVE change a copy
    log.set_logging(log_args)


# TODO TEST
def _main():
    global output_type

    parsed_args = cli_parser.parse_args()

    output_type = parsed_args.kwargs.pop('output')

    log_args = log.LogArgs(
        cmd=parsed_args.cmd,
        **{
            k: parsed_args.kwargs.pop(k) for k in list(parsed_args.kwargs)
            if k in attr.fields_dict(log.LogArgs)
        }
    )

    _set_logging(output_type, log_args)

    general_args = GeneralArgs(
        **{
            k: parsed_args.kwargs.pop(k) for k in list(parsed_args.kwargs)
            if k in attr.fields_dict(GeneralArgs)
        }
    )
    auth_args = AuthArgs(
        **{
            k: parsed_args.kwargs.pop(k) for k in list(parsed_args.kwargs)
            if k in attr.fields_dict(AuthArgs)
        }
    )

    if general_args.version:
        return __version__

    if parsed_args.cmd is None:
        logger.error("Command is required")
        raise ValueError('command is required')

    if auth_args.password == '-':
        auth_args.password = next(fileinput.input(['-'])).rstrip()
    elif auth_args.password is None:
        auth_args.password = os.environ.get('PRVSNR_PASSWORD')

    if auth_args.username:
        auth_init(
            username=auth_args.username,
            password=auth_args.password,
            eauth=auth_args.eauth
        )

    logger.debug(
        f'Parsed arguments: auth={auth_args}, log={log_args}, '
        'cmd={parsed_args.cmd}, args={parsed_args.args}, '
        'kwargs={parsed_args.kwargs}'
    )

    # TODO IMPROVE
    # TODO TEST
    cmd_obj = commands[parsed_args.cmd]
    _args = list(parsed_args.args)
    args, kwargs = runner.SimpleRunner.extract_positional_args(
        parsed_args.kwargs
    )
    _args[0:0] = args
    args, kwargs = cmd_obj.extract_positional_args(kwargs)
    _args[0:0] = args
    args, kwargs = cmd_obj.input_type.extract_positional_args(kwargs)
    _args[0:0] = args

    return _run_cmd(parsed_args.cmd, *_args, **kwargs)


def main():
    ret = None
    exc = None

    try:
        _set_logging(output_type)   # default logging
        ret = _main()
    except BaseException as _exc:
        exc = _exc

        # no sense to dump errors regarding exit
        if isinstance(_exc, SystemExit):
            if not exc.code:
                exc = None
            raise
        else:
            logger.exception('provisioner failed')
            sys.exit(1)
    finally:
        '''
        return format:

        {
            ret: None or <command return>
            exc: None or {
                type:
                args:
                kwargs:
            }
        }

        '''
        if ret is None:
            ret = ''

        if output_type == 'plain':
            if not exc:
                output_res('plain', ret)
        else:
            output_res(
                output_type,
                prepare_res(output_type, ret=ret, exc=exc)
            )


if __name__ == "__main__":
    main()
