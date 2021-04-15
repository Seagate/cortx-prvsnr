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

import argparse
import logging
from pathlib import Path

import toml

from . import defs, __version__
from .server import manage_server, ServerCmdArgs
from .agent import manage_agent, AgentCmdArgs
from .jobs import manage_jobs, JobsCmdArgs

SCRIPT_DIR = Path(__file__).resolve().parent

logging.basicConfig(format=defs.LOGGING_FORMAT, level=defs.LOGLEVEL)

logger = logging.getLogger(__name__)


def dump_config(*args, **kwargs):
    return Path(defs.CONFIG_FILE_EXAMPLE).read_text()


DUMP_CONFIG_CMD = 'dump-config'


class NoArgs:
    pass


cmds_map = {
    'server': (manage_server, ServerCmdArgs),
    'agent': (manage_agent, AgentCmdArgs),
    'jobs': (manage_jobs, JobsCmdArgs),
    DUMP_CONFIG_CMD: (dump_config, NoArgs)
}


def parse_args():
    # COMMON PARSERS
    parser_version = argparse.ArgumentParser(add_help=False)
    parser_version.add_argument(
        "--version", action='store_true',
        help="show version and exit"
    )

    parser_config = argparse.ArgumentParser(add_help=False)
    parser_config.add_argument(
        '-c', '--config',
        metavar="PATH",
        default=str(defs.CONFIG_FILE.relative_to(defs.CWD)),
        help=(
            f"path to a file with {defs.PKGNAME} config."
            f" Consider to use `{DUMP_CONFIG_CMD}` command"
            " to dump an example to standard output"
        )
    )

    # MAIN TOOL PARSER SPEC
    parser = argparse.ArgumentParser(
        description="Simple Cortx Provisioner Jenkins infra tool",
        parents=[parser_version],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        dest='cmd',
        description='Available subcommands'
    )

    #################
    # SERVER PARSER #
    # ###############
    parser_server = subparsers.add_parser(
        'server', description="Jenkins server management",
        help="A set of commands to manage Jenkins servers",
        parents=[parser_config],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser_server.add_argument(
        'action',
        choices=[a.value for a in defs.ServerActionT],
        help="server action to perform"
    )
    parser_server.add_argument(
        '--ssl-domain',
        metavar="domain",
        default=str(defs.LOCALHOST),
        help=(
            "server name protected by the SSL certificate "
            "(aka Common Name or CN)"
        )
    )

    ################
    # AGENT PARSER #
    # #############
    parser_agent = subparsers.add_parser(
        'agent', description="Jenkins agent management",
        help="A set of commands to manage Jenkins agents",
        parents=[parser_config],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser_agent.add_argument(
        'action',
        choices=[a.value for a in defs.AgentActionT],
        help="agent action to perform"
    )
    parser_agent.add_argument(
        '-n', '--name',
        default=None,
        help=(
            "an agent name to use, required for 'connect' action."
            " For 'init' action might be detected automatically"
        )
    )
    parser_agent.add_argument(
        '-w', '--work-dir',
        metavar="PATH",
        default=str(defs.AGENT_WORK_DIR_DEFAULT),
        help=(
            "path to a directory to use as a jenkins root,"
            " will be bind to a container. Should be writeable"
            " for the current user"
        )
    )

    ################
    # JOBS PARSER ##
    # ##############
    parser_jobs = subparsers.add_parser(
        'jobs',
        description='Jenkins jobs management',
        help=(
            "A set of commands to manage Jenkins jobs."
            " Delegates jobs configuration to Jenkins Job Builder (JJB) tool."
            " By default uses the following JJB args: `--recursive`."
            " Additional arguments might be passed as `--args='<args>'`"
        ),
        parents=[parser_config],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser_jobs.add_argument(
        'action',
        choices=[a.value for a in defs.JobsActionT],
        help="jobs action to perform"
    )
    parser_jobs.add_argument(
        '--jjb-args',
        default=None,
        help=(
            "Additional JJB arguments"
        )
    )

    subparsers.add_parser(
        'dump-config',
        description='Dumps configuration example',
        help=(
            "Dumps example configuration to standard output"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    return vars(parser.parse_args())


def parse_config(config: str):
    return toml.loads(Path(config).read_text())


def run(parsed_args):
    if parsed_args.pop('version', False):
        return __version__

    fun, cls = cmds_map[parsed_args.pop('cmd')]

    if 'config' in parsed_args:
        parsed_args['config'] = parse_config(parsed_args['config'])

    return fun(cls(**parsed_args))


def main():
    try:
        parsed_args = parse_args()
        logger.debug(f"Parsed args: {parsed_args}")
        res = run(parsed_args)
    except Exception:
        # logger.exception('failed')
        raise
    else:
        print(res)


if __name__ == "__main__":
    main()
