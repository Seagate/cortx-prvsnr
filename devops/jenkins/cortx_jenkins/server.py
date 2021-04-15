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

import logging
import shutil
import configparser

import attr
import docker

from . import defs
from .utils import run_subprocess_cmd

docker_client = docker.from_env()

logger = logging.getLogger(__name__)


docker_client = docker.from_env()


ServerCmdArgs = attr.make_class(
    'ServerCmdArgs', (
        'config',
        'action',
        'ssl_domain',
    )
)


def build_docker_image(ctx_dir=defs.SERVER_CTX_DIR):
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'build',
        '-t', defs.SERVER_IMAGE_NAME_FULL,
        '-f', str(ctx_dir / defs.SERVER_DOCKERFILE.name),
        str(ctx_dir)
    ])


def start_docker_server():
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'run', '-d',
        '-p', '8083:8083',
        '-p', '50000:50000',
        '-v', f"{defs.SERVER_VOLUME_NAME}:{defs.SERVER_JENKINS_HOME}",
        '--name', defs.SERVER_CONTAINER_NAME,
        defs.SERVER_IMAGE_NAME_FULL
    ])


def build_docker_smeeio_image(ctx_dir=defs.SERVER_CTX_DIR):
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'build',
        '-t', defs.SMEEIO_IMAGE_NAME_FULL,
        '-f', str(ctx_dir / defs.SMEEIO_DOCKERFILE.name),
        str(ctx_dir)
    ])


def start_docker_smeeio():
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'run', '-d',
        '--name', defs.SMEEIO_CONTAINER_NAME,
        defs.SMEEIO_IMAGE_NAME_FULL
    ])


def gen_self_signed_cert(ssl_cn, ctx_dir=defs.SERVER_CTX_DIR, force=False):
    cert_f = ctx_dir / defs.SERVER_HTTPS_CERT_NAME
    rsa_f = ctx_dir / defs.SERVER_HTTPS_RSA_NAME
    pk_f = ctx_dir / defs.SERVER_HTTPS_PK_NAME

    if cert_f.exists() and rsa_f.exists() and (not force):
        logger.debug("https cert exists")
        return

    # 'openssl req' (even with -newkey rsa:4096) creates PKCS#8 private key
    #    (begins with '-----BEGIN PRIVATE KEY-----')
    # and jenkins fails since it expects PKCS#1
    #    (RSA key only, which begins only '-----BEGIN RSA PRIVATE KEY-----').
    # ref: https://issues.jenkins.io/browse/JENKINS-22448
    cert_gen_cmd = [
        'openssl', 'req', '-x509',
        '-newkey', 'rsa:4096',
        '-keyout', str(pk_f),
        '-out', str(cert_f),
        '-days', '365',
        '-nodes',
        '-subj', f"/CN={ssl_cn}"
    ]
    run_subprocess_cmd(cert_gen_cmd)

    rsa_convert_cmd = [
        'openssl', 'rsa',
        '-in', str(pk_f),
        '-out', str(rsa_f)
    ]
    run_subprocess_cmd(rsa_convert_cmd)


def get_container(name):
    try:
        return docker_client.containers.get(name)
    except docker.errors.NotFound:
        logger.debug(
            f"Docker container '{name}' is not found"
        )
        return None


def get_server_container():
    return get_container(defs.SERVER_CONTAINER_NAME)


def get_smeeio_container():
    return get_container(defs.SMEEIO_CONTAINER_NAME)


def start_server():
    start_docker_server()
    start_docker_smeeio()


def prepare_server_ctx(properties, ssl_cn, ctx_dir=defs.SERVER_CTX_DIR):
    ctx_dir.mkdir(parents=True, exist_ok=True)
    for _file in defs.SERVER_DOCKER_CTX_LIST:
        shutil.copy2(_file, ctx_dir / _file.name)

    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    section = 'server'
    config.add_section(section)
    for k, v in properties.items():
        config.set(section, k, str(v))

    with open(ctx_dir / defs.SERVER_PROPERTIES_NAME, 'w') as fh:
        config.write(fh)

    gen_self_signed_cert(ssl_cn, ctx_dir=ctx_dir)


def manage_server(cmd_args: ServerCmdArgs):
    cmd_args.action = defs.ServerActionT(cmd_args.action)

    # TODO copy-paste from agent
    action_map = {
        defs.ServerActionT.STOP: ('stop',),
        defs.ServerActionT.START: ('start',),
        defs.ServerActionT.RESTART: ('restart',),
        defs.ServerActionT.REMOVE: ('stop', 'remove')
    }

    j_server_container = get_server_container()
    smeeio_container = get_server_container()

    if cmd_args.action in action_map:
        if not j_server_container:
            raise RuntimeError('Server container is not found')

        if not smeeio_container:
            logger.warning('Server container is not found')

        logger.info(
            f"Doing server infra {' and '.join(action_map[cmd_args.action])}"
        )
        for action in action_map[cmd_args.action]:
            logger.debug(f"Doing '{action}' for server")
            getattr(j_server_container, action)()
            if smeeio_container:
                logger.debug(f"Doing '{action}' for smeeio")
                getattr(smeeio_container, action)()

        return (j_server_container.name, j_server_container.short_id)

    # cmd_args.action == ServerActionT.CREATE:

    if j_server_container:
        raise RuntimeError(
            'Existent server found, you may consider '
            'to either remove or start it'
        )

    if smeeio_container:
        logger.warning(
            'Existent smeeio found, you may consider '
            'to either remove or start it'
        )

    logger.info('Preparing server docker image context')
    prepare_server_ctx(
        cmd_args.config[defs.ConfigSectionT.SERVER.value],
        cmd_args.ssl_domain
    )

    logger.info('Bulding server docker image')
    build_docker_image()

    logger.info('Bulding smeeio docker image')
    build_docker_smeeio_image()

    logger.info("Starting Jenkins Server infra")
    start_server()
    logger.info("Jenkins Server infra started")

    j_server_container = get_server_container()
    smeeio_container = get_smeeio_container()
    return [
        (j_server_container.name, j_server_container.id),
        (smeeio_container.name, smeeio_container.id),
    ]
