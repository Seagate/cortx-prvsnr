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

import subprocess  # nosec to suppress Bandit
import os
import logging
import docker

from . import defs


logger = logging.getLogger(__name__)


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
        res = subprocess.run(cmd, check=True, **_kwargs)  # nosec to suppress Bandit
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


def set_ssl_verify(verify):
    if not verify:
        logger.warning("Turning off HTTPS SSL verification")
    # TODO find (update when appear) the better way how
    #      to set that for python-jenkins package, current workaround
    #      refers https://opendev.org/jjb/python-jenkins/src/commit/570a143c74d092efaf9bc68a3bae9b15804f4a63/jenkins/__init__.py#L345-L348  # noqa: E501
    os.environ['PYTHONHTTPSVERIFY'] = ('1' if verify else '0')


def get_server_bridge_ip():
    docker_client = docker.from_env()

    j_server_container = docker_client.containers.get(
        defs.SERVER_CONTAINER_NAME
    )
    return j_server_container.attrs[
        'NetworkSettings']['Networks']['bridge']['IPAddress']
