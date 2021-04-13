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

import attr
import docker

from . import defs
from .utils import run_subprocess_cmd

docker_client = docker.from_env()

logger = logging.getLogger(__name__)


docker_client = docker.from_env()


ServerCmdArgs = attr.make_class(
    'ServerCmdArgs', (
        'action',
        # 'verbose',
        'properties',
        'ssl_domain'
    )
)


def build_docker_image(ctx_dir=defs.SERVER_CTX_DIR):
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'build',
        '-t', defs.SERVER_IMAGE_NAME_FULL,
        '-f', ctx_dir / defs.SERVER_DOCKERFILE.name,
        ctx_dir
    ])


def start_docker_server():
    # TODO use docker python wrapper
    run_subprocess_cmd([
        'docker', 'run', '-d',
        '-p', '8080:8080',
        '-p', '8083:8083',
        '-p', '50000:50000',
        '-v', f"{defs.SERVER_VOLUME_NAME}:{defs.SERVER_JENKINS_HOME}",
        '--name', defs.SERVER_CONTAINER_NAME,
        defs.SERVER_IMAGE_NAME_FULL
    ])


def gen_self_signed_cert(ssl_cn, ctx_dir=defs.SERVER_CTX_DIR, force=False):
    cert_f = ctx_dir / defs.SERVER_HTTPS_CERT_NAME
    rsa_f = ctx_dir / defs.SERVER_HTTPS_RSA_NAME
    pk_f = ctx_dir / defs.SERVER_HTTPS_PK_NAME

    if cert_f.exists() and rsa_f.exists() and (not force):
        logger.debug(f"https cert exists")
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


def get_server_container():
    try:
        return docker_client.containers.get(
            defs.SERVER_CONTAINER_NAME
        )
    except docker.errors.NotFound:
        logger.debug(
            f"Docker container with '{defs.SERVER_CONTAINER_NAME}'"
            " is not found"
        )
        return None


def start_server():
    start_docker_server()


def prepare_server_ctx(properties, ssl_cn, ctx_dir=defs.SERVER_CTX_DIR):
    ctx_dir.mkdir(parents=True, exist_ok=True)
    for _file in defs.SERVER_DOCKER_CTX_LIST:
        shutil.copy2(_file, ctx_dir / _file.name)

    shutil.copy2(properties, ctx_dir / defs.SERVER_INPUTS.name)

    gen_self_signed_cert(ssl_cn, ctx_dir=ctx_dir)


def manage_server(cmd_args):
    cmd_args.action = defs.ServerActionT(cmd_args.action)

    # TODO copy-paste from agent
    action_map = {
        defs.ServerActionT.STOP: ('stop',),
        defs.ServerActionT.START: ('start',),
        defs.ServerActionT.RESTART: ('restart',),
        defs.ServerActionT.REMOVE: ('stop', 'remove')
    }

    j_server_container = get_server_container()

    if cmd_args.action in action_map:
        if not j_server_container:
            raise RuntimeError('Server container is not found')

        logger.info(
            f"Doing server {' and '.join(action_map[cmd_args.action])}"
        )
        for action in action_map[cmd_args.action]:
            getattr(j_server_container, action)()

        return (j_server_container.name, j_server_container.short_id)

    # cmd_args.action == ServerActionT.CREATE:

    if j_server_container:
        raise RuntimeError(
            'Existent server found, you may consider '
            'to either remove or start it'
        )

    logger.info('Preparing server docker image context')
    prepare_server_ctx(cmd_args.properties, cmd_args.ssl_domain)

    logger.info('Bulding server docker image')
    build_docker_image()

    logger.info("Starting Jenkins server")
    start_server()
    logger.info("Jenkins Server started")

    j_server_container = get_server_container()
    return (j_server_container.name, j_server_container.id)
