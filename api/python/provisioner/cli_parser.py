#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import logging
import attr

from . import config, errors, runner, log
from .base import prvsnr_config
from .commands import commands

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


def parse_args(args=None):
    parser_common = argparse.ArgumentParser(add_help=False)

    general_group = parser_common.add_argument_group('general')
    general_group.add_argument(
        "--version", action='store_true',
        help="show version and quit"
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

    parser = ErrorHandlingArgumentParser(
        verbose=(
            prvsnr_config.env['PRVSNR_OUTPUT']
            not in config.PRVSNR_CLI_MACHINE_OUTPUT
        ),
        description="Provisioner CLI",
        parents=[parser_common],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(
        dest='command',
        title='sub commands',
        description='valid subcommands'
    )

    # TODO description and help strings
    for cmd_name, cmd in commands.items():
        subparser = subparsers.add_parser(
            cmd_name, description='{} configuration'.format(cmd_name),
            help='{} help'.format(cmd_name), parents=[parser_common],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        cmd.fill_parser(subparser)
        cmd.input_type.fill_parser(subparser)

    kwargs = vars(parser.parse_args(args=args))
    cmd = kwargs.pop('command')
    args = kwargs.pop('args', [])
    return ParseRes(cmd, args, kwargs)
