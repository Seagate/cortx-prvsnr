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
import time
import subprocess
import sys


logger = logging.getLogger(__name__)

def run_subprocess_cmd(cmd, **kwargs):
    """
    This function runs the command on the prompt using subprocess.run()
    It returns the result or exception in the form of dictionary
    """
    _kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    _kwargs.update(kwargs)
    _kwargs['check'] = True

    if not _kwargs.get('timeout', None):
        _kwargs['timeout'] = 15
    if isinstance(cmd, str):
        cmd = cmd.split()

    try:
        logger.debug(f"Subprocess - command: '{cmd}', kwargs: '{_kwargs}'")
        res = subprocess.run(cmd, **_kwargs)
    except subprocess.TimeoutExpired as exc:
        result = (1, str(exc), repr(exc))
        logger.error(f"Subprocess command resulted in: {result}")
    except Exception as exc:
        result = (exc.returncode, str(exc), repr(exc))
        logger.error(f"Subprocess command resulted in: {result}")
    else:
        logger.debug(f"Subprocess command resulted in: {res}")
        result = (res.returncode, res.stdout, res.stderr)
    return {
            "ret_code": result[0],
            "response": result[1],
            "error_msg": result[2],
            "message": ""
        }


def remote_execution(remote_ip, cmd):
    """This function executes command on remote node."""
    ssh_cmd="ssh -i /root/.ssh/id_rsa_prvsnr -o StrictHostKeyChecking=no"
    cmd = f'{ssh_cmd} {remote_ip} {cmd}'
    return run_subprocess_cmd(cmd)
