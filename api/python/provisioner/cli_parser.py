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


import sys
import argparse
import logging
from typing import List, Optional

from .vendor import attr
from . import config, errors, runner, log
from .base import prvsnr_config

logger = logging.getLogger(__name__)

ParseRes = attr.make_class("ParseRes", ('cmd', 'args', 'kwargs'))


# TODO TEST EOS-7495
class ErrorHandlingArgumentParser(argparse.ArgumentParser):

    def __init__(self, verbose=True, *args, **kwargs):
        self.verbose = verbose
        super().__init__(*args, **kwargs)

    def exit(self, status=0, message=None):
        if status:
            raise errors.ProvisionerCliError(f'Parse args error: {message}')
        sys.exit(0)

    def error(self, message):
        if self.verbose:
            self.print_usage(sys.stderr)
            # TODO IMPROVE non-api usage
            self._print_message(
                '{} error: {}\n'.format(self.prog, message),
                sys.stderr
            )

        self.exit(2, message)

    def print_help(self, *args, **kwargs):
        if self.verbose:
            super().print_help(*args, **kwargs)


class KeyValueListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        res = getattr(namespace, self.dest, {})

        if not isinstance(res, (dict, type(None))):
            raise TypeError(
                f"value for {self.dest} should be a dictionary or None, "
                f"provided: {type(res)}"
            )

        if res is None:
            res = {}

        if values:
            for kv in values:
                k, v = kv.split("=", 1)
                res[k.strip()] = v

        setattr(namespace, self.dest, res)


def parse_args(args=None, commands: Optional[List] = None):
    parser_common = argparse.ArgumentParser(add_help=False)

    general_group = parser_common.add_argument_group('general')
    general_group.add_argument(
        "--version", action='store_true',
        help="show version and exit"
    )

    auth_group = parser_common.add_argument_group('authentication')
    auth_group.add_argument(
        "--username", metavar="STR", default=None,
        help="username"
    )
    auth_group.add_argument(
        "--password", metavar="STR", default=None,
        help=(
            "password, '-' means read from stdin. "
            "Another option is to use PRVSNR_PASSWORD env variable"
        )
    )
    auth_group.add_argument(
        "--eauth", default='pam', choices=['pam', 'ldap'],
        help="type of external authentication to use"
    )

    log_group = parser_common.add_argument_group('output & logging')
    log_group.add_argument(
        "--output", default=prvsnr_config.env['PRVSNR_OUTPUT'],
        choices=config.PRVSNR_CLI_OUTPUT,
        help="result output format"
    )
    log.LogArgs.fill_parser(log_group)

    cmd_runner_group = parser_common.add_argument_group(
        'common command running arguments'
    )
    runner.SimpleRunner.fill_parser(cmd_runner_group)

    common_parsers = [parser_common]

    parser = ErrorHandlingArgumentParser(
        verbose=(
            prvsnr_config.env['PRVSNR_OUTPUT']
            not in config.PRVSNR_CLI_MACHINE_OUTPUT
        ),
        description="CORTX Provisioner CLI",
        parents=common_parsers,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    if commands:
        subparsers = parser.add_subparsers(
            dest='command',
            title='sub commands',
            description='valid subcommands'
        )

        # TODO description and help strings
        for cmd_name, cmd in commands.items():
            desc = getattr(cmd, 'description', f'{cmd_name} configuration')

            subparser = subparsers.add_parser(
                cmd_name, description='{}'.format(desc),
                help='{} help'.format(cmd_name), parents=common_parsers,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            cmd.fill_parser(subparser, list(common_parsers))
            cmd.input_type.fill_parser(subparser)

    kwargs = vars(parser.parse_args(args=args))
    cmd = kwargs.pop('command')
    args = kwargs.pop('args', [])
    return ParseRes(cmd, args, kwargs)
