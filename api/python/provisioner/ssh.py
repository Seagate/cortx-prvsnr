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

import logging
import os
from pathlib import Path
from typing import Union

from .utils import run_subprocess_cmd

logger = logging.getLogger(__name__)


# TODO TEST EOS-8473
def keygen(
    priv_key_path: Union[Path, str],
    comment: str = '',
    passphrase: str = ''
):
    run_subprocess_cmd(
        (
            "ssh-keygen -t rsa -b 4096 -o -a 100".split() +
            ['-C', comment, '-N', passphrase, '-f', str(priv_key_path)]
        ),
        input='y'
    )


# TODO TEST EOS-8473
def copy_id(
    host: str,
    user: str = None,
    port: int = None,
    priv_key_path: Union[Path, str] = None,
    force=False,
    ssh_options=None,
):
    cmd = ['ssh-copy-id']

    if force:
        cmd.append('-f')

    if priv_key_path:
        cmd.extend(['-i', str(priv_key_path)])

    if port:
        cmd.extend(['-p', str(port)])

    if ssh_options is not None:
        for opt in ssh_options:
            cmd.extend(['-o', opt])

    cmd.append(f"{user}@{host}" if user else f"{host}")

    auto_ssh = ['sshpass', '-e'] if os.environ["SSHPASS"] else ''
    cmd = auto_ssh + cmd

    logger.info("Copying keys for ssh password-less connectivity.")
    logger.debug(f"Command: {cmd}")
    run_subprocess_cmd(cmd)
