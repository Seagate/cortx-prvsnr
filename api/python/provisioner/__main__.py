#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
#


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
    log,
    cli_parser,
    utils
)
from .commands import commands
from .commands.setup_provisioner import (
    SetupCmdBase, RunArgsSetupProvisionerGeneric
)
from .base import prvsnr_config

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
            "Invalid output format provided: '{}'. "
            "Output type can be yaml or json or just plain."
            .format(output_type)
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


def _set_logging(output_type, log_args=None, other_args=None):  # noqa: C901
    if log_args is None:
        log_args = log.LogArgs()

    # forcing some log settings based on output type
    #   disable console log handler for machine readable output
    if output_type in config.PRVSNR_CLI_MACHINE_OUTPUT:
        if hasattr(log_args, config.LOG_CONSOLE_HANDLER):
            setattr(log_args, config.LOG_CONSOLE_HANDLER, False)

    # forcibly enable and configure rotation file logging
    #   - for most important commands
    #   - for setup commands
    # forcibly disable rsyslog
    #   - for setup commands
    cmd = getattr(log_args, 'cmd', None)
    cmd_inst = commands.get(cmd)

    if (
        hasattr(log_args, config.LOG_RSYSLOG_HANDLER)
        and isinstance(cmd_inst, SetupCmdBase)
    ):
        # disable rsyslog logging
        setattr(log_args, config.LOG_RSYSLOG_HANDLER, False)
        log_args.update_handlers()

    if (
        cmd in config.LOG_FORCED_LOGFILE_CMDS
        # or isinstance(cmd_inst, SetupCmdBase)  FIXME EOS-13228 regression
    ):
        if hasattr(log_args, config.LOG_FILE_HANDLER):
            # enable file logging
            setattr(log_args, config.LOG_FILE_HANDLER, True)

            setattr(log_args, config.LOG_FILE_SALT_HANDLER, True)
            # set file to log if default value is set
            filename_attr = f'{config.LOG_FILE_HANDLER}_filename'
            if (
                getattr(log_args, filename_attr) ==
                attr.fields_dict(type(log_args))[filename_attr].default
            ):
                # FIXME EOS-13228 regression
                if isinstance(cmd_inst, SetupCmdBase) and False:
                    # TODO IMPROVE EOS-13228 not a clean way to check
                    #      other args here, logging was supposed to be
                    #      agnostic to commands
                    run_args = RunArgsSetupProvisionerGeneric(
                        **{
                            k: other_args.kwargs.get(k) for k in list(
                                other_args.kwargs
                            )
                            if k in attr.fields_dict(
                                RunArgsSetupProvisionerGeneric
                            )
                        }
                    )
                    profile_dir = (
                        SetupCmdBase.setup_location(run_args) /
                        SetupCmdBase.setup_name(run_args)
                    )
                    profile_dir.mkdir(parents=True, exist_ok=True)
                    filename = profile_dir / f"{cmd}.log"
                else:
                    filename = _generate_logfile_filename(log_args.cmd)
                setattr(log_args, filename_attr, str(filename))

    if (cmd in config.LOG_SUPPRESSION_CMDS and
            hasattr(log_args, config.LOG_RSYSLOG_HANDLER)):
        setattr(log_args, config.LogLevelTypes.RSYSLOG.value, logging.WARNING)
    elif hasattr(log_args, config.LOG_FILE_HANDLER):
        pass  # just to signalize that log_args.update_handlers() is needed
    else:
        log.set_logging(log_args)
        return

    log_args.update_handlers()

    # TODO IMPROVE change a copy
    log.set_logging(log_args)


# TODO TEST
def _main():
    global output_type

    parsed_args = cli_parser.parse_args(commands=commands)

    output_type = parsed_args.kwargs.pop('output')

    log_args_view = {
        k: parsed_args.kwargs.pop(k) for k in list(parsed_args.kwargs)
        if k in attr.fields_dict(log.LogArgs)
    }

    log_args = log.LogArgs(
        cmd=parsed_args.cmd, **log_args_view
    )

    # TODO IMPROVE EOS-14361 configure salt loggers
    #      for secure levels if needed
    _set_logging(output_type, log_args, parsed_args)

    # TODO make that configuration smarter
    #      (one may need this noisy logs in some case)
    utils.make_salt_logs_quiet()

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

    logger.info(f"Running provisioner version: {__version__}")

    if parsed_args.cmd is None:
        logger.error("No command Provided. "
                     "A valid command is required to process further..")
        raise ValueError("Empty command argument encountered")

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

    auth_args_view = attr.asdict(auth_args)
    if auth_args_view['password']:
        auth_args_view['password'] = config.SECRET_MASK

    logger.debug(
        "\nParsed arguments: \n"
        f"auth={auth_args_view}, \n"
        f"log={log_args_view}, \n"
        f"cmd={parsed_args.cmd}, \n"
        f"args={parsed_args.args}, \n"
        f"kwargs={parsed_args.kwargs} \n"
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
            logger.exception(
               "PROVISIONER FAILED.\n"
               f"Reason: {exc}\n"
               "Exiting now.."
            )
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
