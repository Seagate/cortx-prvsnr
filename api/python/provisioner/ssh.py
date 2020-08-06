#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging
from pathlib import Path
from typing import Union

from .utils import run_subprocess_cmd

logger = logging.getLogger(__name__)


# TODO TEST CORTX-8473
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


# TODO TEST CORTX-8473
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

    cmd.append(f"{user}@{host}" if user else host)

    run_subprocess_cmd(cmd)
