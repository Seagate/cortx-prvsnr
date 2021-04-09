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
import os
import subprocess
import logging
import re
from enum import Enum
from pathlib import Path

import jenkins
import requests
import attr
import docker

SCRIPT_DIR = Path(__file__).resolve().parent

CREDS_FILE_DEFAULT = SCRIPT_DIR / 'credentials'
WORK_DIR_DEFAULT = '/var/lib/jenkins'
JENKINS_URL_DEFAULT = 'http://localhost:8080/'


IMAGE_VERSION = '0.0.1'
IMAGE_NAME = 'seagate/cortx-prvsnr-jenkins-inbound-agent'
IMAGE_TAG = IMAGE_VERSION
IMAGE_NAME_FULL = f"{IMAGE_NAME}:{IMAGE_VERSION}"

CONTAINER_NAME = 'cortx-prvsnr-jenkins-agent'
SERVER_CONTAINER_NAME = 'cortx-prvsnr-jenkins'

DOCKERFILE = SCRIPT_DIR / 'Dockerfile.inbound-agent'
DOCKER_CTX_DIR = SCRIPT_DIR
DOCKER_SOCKET = Path('/var/run/docker.sock')

LOGGING_FORMAT = '%(asctime)s - %(thread)d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d]: %(message)s'  # noqa: E501
LOGLEVEL_DEFAULT = 'WARNING'
LOGLEVEL = os.getenv('LOGLEVEL', LOGLEVEL_DEFAULT)

MASTER_AGENT = 'master'
EXPECTED_AGENT_LABELS = set(['cortx-prvsnr-ci'])

LOCALHOST = 'localhost'

AGENT_CONFIG_REGEX = re.compile(
    r'.*<application-desc main-class="hudson.remoting.jnlp.Main"><argument>'
    r'([a-z0-9]*).*<argument>-workDir<\/argument><argument>([^<]*).*'
)

docker_client = docker.from_env()


class AgentActionT(Enum):
    """Jenkins agent actions"""
    CREATE = "create"
    STOP = "stop"
    START = "start"
    RESTART = "restart"
    REMOVE = "remove"


logging.basicConfig(format=LOGGING_FORMAT, level=LOGLEVEL)

logger = logging.getLogger(__name__)


class NoOfflineAgentError(RuntimeError):
    pass


CmdArgs = attr.make_class(
    'CmdArgs', (
        'action',
        'creds_file',
        'name',
        'work_dir',
        'verbose',
        'jenkins_url'
    )
)

AgentConfig = attr.make_class(
    'AgentConfig', (
        'secret', 'work_dir'
    )
)

AgentData = attr.make_class(
    'AgentData', (
        'name', 'config'
    )
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple Cortx Provisioner Jenkins Agents Manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'action',
        choices=[a.value for a in AgentActionT],
        help="agent action to perform"
    )
    parser.add_argument(
        '-c', '--creds-file',
        metavar="PATH",
        default=str(CREDS_FILE_DEFAULT),
        help=(
            "path to a file with jenkins user credentials"
            " with Agent:Connect and Agent:Create permissions."
            " Format: USER:APITOKEN in the first line"
        )
    )
    parser.add_argument(
        '-n', '--name',
        default=None,
        help=(
            "an agent name to use, required for 'connect' action."
            " For 'init' action might be detected automatically"
        )
    )
    parser.add_argument(
        '-w', '--work-dir',
        metavar="PATH",
        default=str(WORK_DIR_DEFAULT),
        help=(
            "path to a directory to use as a jenkins root,"
            " will be bind to a container. Should be writeable"
            " for the current user"
        )
    )
    parser.add_argument(
        '-s', '--jenkins-url',
        default=str(JENKINS_URL_DEFAULT),
        help="Jenkins server url"
    )
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="be more verbose"
    )

    return vars(parser.parse_args())


def run_subprocess_cmd(cmd, **kwargs):
    _kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    _kwargs.update(kwargs)
    _kwargs.pop('check', None)

    if isinstance(cmd, str):
        cmd = cmd.split()

    try:
        logger.debug(f"Subprocess command {cmd}, kwargs: {_kwargs}")
        res = subprocess.run(cmd, check=True, **_kwargs)
    except subprocess.CalledProcessError as exc:
        logger.exception(f"Failed to run cmd '{cmd}, stderr: '{exc.stderr}''")
        raise
    else:
        logger.debug(
            f"Subprocess command {res.args} "
            f"resulted in - stdout: {res.stdout}, "
            f"returncode: {res.returncode}, stderr: {res.stderr}"
        )
        return res


def build_docker_image():
    uid = os.getuid()
    gid = os.getgid()

    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'build',
        '-t', IMAGE_NAME_FULL,
        '--build-arg', f"uid={uid}",
        '--build-arg', f"gid={gid}",
        '-f', DOCKERFILE,
        DOCKER_CTX_DIR
    ])


def start_docker_agent(work_dir, j_url, a_secret, a_name):
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'run', '--init', '-d',
        '-v', f"{DOCKER_SOCKET}:{DOCKER_SOCKET}",
        '-v', f"{work_dir}:{work_dir}",
        '--name', CONTAINER_NAME,
        IMAGE_NAME_FULL,
        '-url', j_url,
        '-workDir', work_dir,
        a_secret, a_name
    ])


def get_agent_config(server, agent):
    # resolve an agent secret
    # TODO check more for ready wrapper over that
    req = requests.Request(
        'GET', f"{server.server}/computer/{agent}/jenkins-agent.jnlp"
    )
    resp = server.jenkins_request(req)

    # TODO use xml parser (??? known XML vulnerabilities)
    match = AGENT_CONFIG_REGEX.search(resp.text)
    return AgentConfig(match.group(1), match.group(2)) if match else None


def resolve_free_offline_agent(server):
    agents = server.get_nodes()
    logger.debug(f"List of jenkins agents: {agents}")

    candidate = None
    config = None
    for agent in agents:
        candidate = agent['name']

        if not (candidate != MASTER_AGENT and agent['offline']):
            continue

        a_info = server.get_node_info(candidate)
        a_labels = [label['name'] for label in a_info['assignedLabels']]

        if (
            a_info['jnlpAgent']
            and not a_info['temporarilyOffline']
            and (EXPECTED_AGENT_LABELS & set(a_labels))
        ):
            config = get_agent_config(server, candidate)
            if config:
                break
    else:
        raise NoOfflineAgentError(
            'no offline agent with acceptable parameters'
        )

    return AgentData(candidate, config)


def get_agent_container():
    try:
        return docker_client.containers.get(
            CONTAINER_NAME
        )
    except docker.errors.NotFound:
        logger.debug(f"Docker container with '{CONTAINER_NAME}' is not found")
        return None


def start_agent(j_url, agent_data):
    if LOCALHOST in j_url:
        j_server_container = docker_client.containers.get(
            SERVER_CONTAINER_NAME
        )
        j_server_bridge_ip = j_server_container.attrs[
            'NetworkSettings']['Networks']['bridge']['IPAddress']
        j_url = j_url.replace(LOCALHOST, j_server_bridge_ip)

    start_docker_agent(
        agent_data.config.work_dir,
        j_url,
        agent_data.config.secret,
        agent_data.name
    )


def main():
    parsed_args = parse_args()
    logger.debug(f"Parsed args: {parsed_args}")

    # TODO move to attr-based spec
    cmd_args = CmdArgs(**parsed_args)
    cmd_args.action = AgentActionT(cmd_args.action)

    action_map = {
        AgentActionT.STOP: ('stop',),
        AgentActionT.START: ('start',),
        AgentActionT.RESTART: ('restart',),
        AgentActionT.REMOVE: ('stop', 'remove')
    }

    j_agent_container = get_agent_container()

    if cmd_args.action in action_map:
        if not j_agent_container:
            raise RuntimeError('Agent container is not found')

        logger.info(
            f"Doing agent {'and'.join(action_map[cmd_args.action])}"
        )
        for action in action_map[cmd_args.action]:
            getattr(j_agent_container, action)()

        return (j_agent_container.name, j_agent_container.id)

    # cmd_args.action == AgentActionT.CREATE:

    if j_agent_container:
        raise RuntimeError(
            'Existent agent found, you may consider '
            'to either remove or start it'
        )

    with open(cmd_args.creds_file) as _creds_f:
        j_user, j_token = [
            part.strip() for part in _creds_f.readline().split(':')
        ]
    logger.debug(f"Using jenkins user '{j_user}' credentials")

    logger.info('Bulding agent docker image')
    build_docker_image()

    server = jenkins.Jenkins(
        cmd_args.jenkins_url, username=j_user, password=j_token
    )

    if not cmd_args.name:
        logger.info('Resolving free prepared agent slot')
        agent_data = resolve_free_offline_agent(server)
        logger.debug(f"\tFound free agent '{agent_data.name}'")
    else:
        logger.info(f"Resolving '{cmd_args.name}' agent data")
        agent_data = AgentData(
            cmd_args.name, get_agent_config(server, cmd_args.name)
        )

    if agent_data.config.work_dir != cmd_args.work_dir:
        logger.warning(
            f"Specified working directory '{cmd_args.work_dir}' doesn't match"
            f" remote agent setting '{agent_data.config.work_dir}'"
        )

    logger.info(
        f"Starting agent '{agent_data.name}' with working"
        f" directory {agent_data.config.work_dir}"
    )
    start_agent(cmd_args.jenkins_url, agent_data)
    logger.info(f"Agent '{agent_data.name}' launched")

    j_agent_container = get_agent_container()
    return (j_agent_container.name, j_agent_container.id)


if __name__ == "__main__":
    try:
        res = main()
    except Exception:
        # logger.exception('failed')
        raise
    else:
        print(res)
