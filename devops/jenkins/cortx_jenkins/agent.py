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
import logging
import shutil

import jenkins
import requests
import attr
import docker

from . import defs, utils

docker_client = docker.from_env()

logger = logging.getLogger(__name__)


class NoOfflineAgentError(RuntimeError):
    pass


AgentCmdArgs = attr.make_class(
    'AgentCmdArgs', (
        'config',
        'action',
        'name',
        'work_dir'
    )
)


docker_client = docker.from_env()

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


def build_docker_image():
    uid = os.getuid()
    gid = os.getgid()

    # TODO use docker python wrapper
    utils.run_subprocess_cmd([
        'docker', 'build',
        '-t', defs.AGENT_IMAGE_NAME_FULL,
        '--build-arg', f"uid={uid}",
        '--build-arg', f"gid={gid}",
        '-f', str(defs.AGENT_DOCKERFILE),
        str(defs.AGENT_DOCKER_CTX_DIR)
    ])


def start_docker_agent(work_dir, j_url, a_secret, a_name):
    # TODO use docker python wrapper
    utils.run_subprocess_cmd([
        'docker', 'run', '--init', '-d',
        '-v', f"{defs.DOCKER_SOCKET}:{defs.DOCKER_SOCKET}",
        '-v', f"{work_dir}:{work_dir}",
        '--name', defs.AGENT_CONTAINER_NAME,
        defs.AGENT_IMAGE_NAME_FULL,
        '-url', j_url,
        '-workDir', str(work_dir),
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
    match = defs.AGENT_CONFIG_REGEX.search(resp.text)
    return AgentConfig(match.group(1), match.group(2)) if match else None


def resolve_free_offline_agent(server):
    agents = server.get_nodes()
    logger.debug(f"List of jenkins agents: {agents}")

    candidate = None
    a_config = None
    for agent in agents:
        candidate = agent['name']

        if not (candidate != defs.MASTER_AGENT and agent['offline']):
            continue

        a_info = server.get_node_info(candidate)
        a_labels = [label['name'] for label in a_info['assignedLabels']]

        if (
            a_info['jnlpAgent']
            and not a_info['temporarilyOffline']
            and (defs.EXPECTED_AGENT_LABELS & set(a_labels))
        ):
            a_config = get_agent_config(server, candidate)
            if a_config:
                break
    else:
        raise NoOfflineAgentError(
            'no offline agent with acceptable parameters'
        )

    return AgentData(candidate, a_config)


def get_agent_container():
    try:
        return docker_client.containers.get(
            defs.AGENT_CONTAINER_NAME
        )
    except docker.errors.NotFound:
        logger.debug(
            f"Docker container with '{defs.AGENT_CONTAINER_NAME}'"
            " is not found"
        )
        return None


def start_agent(j_url, agent_data):
    if defs.LOCALHOST in j_url:
        j_server_container = docker_client.containers.get(
            defs.SERVER_CONTAINER_NAME
        )
        j_server_bridge_ip = j_server_container.attrs[
            'NetworkSettings']['Networks']['bridge']['IPAddress']
        j_url = j_url.replace(defs.LOCALHOST, j_server_bridge_ip).replace(
            'https:', 'http:').replace(':8083', ':8080')

    start_docker_agent(
        agent_data.config.work_dir,
        j_url,
        agent_data.config.secret,
        agent_data.name
    )


def prepare_agent_ctx(ctx_dir=defs.AGENT_CTX_DIR):
    ctx_dir.mkdir(parents=True, exist_ok=True)
    for _file in defs.AGENT_DOCKER_CTX_LIST:
        shutil.copy2(_file, ctx_dir / _file.name)


def manage_agent(cmd_args: AgentCmdArgs):
    cmd_args.action = defs.AgentActionT(cmd_args.action)

    action_map = {
        defs.AgentActionT.STOP: ('stop',),
        defs.AgentActionT.START: ('start',),
        defs.AgentActionT.RESTART: ('restart',),
        defs.AgentActionT.REMOVE: ('stop', 'remove')
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

        return (j_agent_container.name, j_agent_container.short_id)

    # cmd_args.action == AgentActionT.CREATE:

    if j_agent_container:
        raise RuntimeError(
            'Existent agent found, you may consider '
            'to either remove or start it'
        )

    global_config = cmd_args.config[defs.ConfigSectionT.GLOBAL.value]
    agent_config = cmd_args.config[defs.ConfigSectionT.AGENT.value]

    j_user = (
        agent_config.get('username') or global_config.get('username')
    )
    j_token = (
        agent_config.get('token') or global_config.get('token')
    )
    j_url = (
        agent_config.get('url') or global_config.get('url')
    )
    logger.debug(
        f"Using jenkins user '{j_user}' credentials, server url '{j_url}'"
    )

    utils.set_ssl_verify(global_config['ssl_verify'])

    logger.info('Preparing agent docker image context')
    prepare_agent_ctx()

    logger.info('Bulding agent docker image')
    build_docker_image()

    server = jenkins.Jenkins(
        j_url, username=j_user, password=j_token
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
    start_agent(j_url, agent_data)
    logger.info(f"Agent '{agent_data.name}' started")

    j_agent_container = get_agent_container()
    return (j_agent_container.name, j_agent_container.id)
