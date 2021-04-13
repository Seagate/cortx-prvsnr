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

from . import defs
from .server import manage_server, ServerCmdArgs
from .agent import manage_agent, AgentCmdArgs
from .jobs import manage_jobs, JobsCmdArgs

SCRIPT_DIR = Path(__file__).resolve().parent

logging.basicConfig(format=defs.LOGGING_FORMAT, level=defs.LOGLEVEL)

logger = logging.getLogger(__name__)


cmds_map = {
    'server': (manage_server, ServerCmdArgs),
    'agent': (manage_agent, AgentCmdArgs),
    'jobs': (manage_jobs, JobsCmdArgs),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple Cortx Provisioner Jenkins infra tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        dest='cmd',
        description='Available subcommands'
    )

    # SERVER PARSER
    parser_server = subparsers.add_parser(
        'server', description="Jenkins server management",
        help="A set of commands to manage Jenkins servers",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_server.add_argument(
        '-p', '--properties',
        metavar="PATH",
        default=str(defs.SERVER_INPUTS),
        help=(
            "path to a file with jenkins server properties"
            " (including necessary credentials and other secrets)"
        )
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

    parser_server.add_argument(
        'action',
        choices=[a.value for a in defs.ServerActionT],
        help="server action to perform"
    )

    # AGENT PARSER
    parser_agent = subparsers.add_parser(
        'agent', description="Jenkins agent management",
        help="A set of commands to manage Jenkins agents",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser_agent.add_argument(
        'action',
        choices=[a.value for a in defs.AgentActionT],
        help="agent action to perform"
    )
    parser_agent.add_argument(
        '-c', '--creds-file',
        metavar="PATH",
        default=str(defs.CREDS_FILE_DEFAULT),
        help=(
            "path to a file with jenkins user credentials"
            " with Agent:Connect and Agent:Create permissions."
            " Format: USER:APITOKEN in the first line"
        )
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
    parser_agent.add_argument(
        '-s', '--jenkins-url',
        default=str(defs.JENKINS_URL_DEFAULT),
        help="Jenkins server url"
    )

    # parser_agent.add_argument(
    #     '-v', '--verbose', action="store_true",
    #     help="be more verbose"
    # )

    # JOBS PARSER
    parser_jobs = subparsers.add_parser(
        'jobs',
        description='Jenkins jobs management',
        help=(
            "A set of commands to manage Jenkins jobs"
            " Delegates jobs configuration to Jenkins Job Builder (JJB) tool."
            " By default uses the following JJB args: `--recursive`."
            " Additional arguments might be passed as `--args='<args>'`"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser_jobs.add_argument(
        'action',
        choices=[a.value for a in defs.JobsActionT],
        help="jobs action to perform"
    )
    parser_jobs.add_argument(
        '-c', '--ini-file',
        metavar="PATH",
        default=str(defs.JOBS_CONFIG),
        help=(
            "path to a file with jenkins jobs config."
            f" Consider to use `{defs.JobsActionT.CONFIG_DUMP.value}` "
            "action to create an example one"
        )
    )
    parser_jobs.add_argument(
        '--jjb-args',
        default=None,
        help=(
            "Additional JJB arguments"
        )
    )

    return vars(parser.parse_args())


def main():
    parsed_args = parse_args()

    logger.debug(f"Parsed args: {parsed_args}")

    try:
        cmd = cmds_map[parsed_args.pop('cmd')]
        res = cmd[0](cmd[1](**parsed_args))
    except Exception:
        # logger.exception('failed')
        raise
    else:
        print(res)


if __name__ == "__main__":
    main()
