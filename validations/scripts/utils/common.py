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
import subprocess
import paramiko
import time
from messages.user_messages import *

logger = logging.getLogger(__name__)


def run_subprocess_cmd(cmd, **kwargs):
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
        logger.debug(f"Subprocess command {cmd}, kwargs: {_kwargs}")
        res = subprocess.run(cmd, **_kwargs)
    except subprocess.TimeoutExpired as exc:
        result = (1, str(exc), repr(exc))
        logger.error(f"Subprocess command resulted in: {result}")
    except Exception as exc:
        result = (1, str(exc), repr(exc))
        logger.error(f"Subprocess command resulted in: {result}")
    else:
        logger.debug(f"Subprocess command resulted in: {res}")
        result = (res.returncode, res.stdout, res.stderr)
    return result


def ssh_remote_machine(hostname, username, password, port=None):
    cmd = "pip3 install paramiko"
    self.run_subprocess_cmd(cmd)
    time.sleep(5)
    ssh_client = paramiko.client.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #ssh_client=paramiko.SSHClient(paramiko.AutoAddPolicy())
    res = ssh_client.connect(hostname, port, username, password)
    print (res)
    if res:
        stdin, stdout, stderr = ssh_client.exec_command(
            'hostname', bufsize=-1, timeout=None, get_pty=False)
        print (stdin, stdout, stderr)
        for line in stdout:
            result = line.strip('\n')
        print (result)
        response[1] = f"SSH Success for: {hostname}"
        response[0] = 0
        return result
    else:
        result = str(SSH_CONN_ERROR)
        response[2] = f"SSH Failed for: {hostname}"
        response[0] = 1
    ssh_client.close()
    return  {"ret_code": response[0],
            "response": response[1],
            "error_msg": response[2],
            "message": str(result)}


def decrypt_secret(auth_key, secret):
    """Decrypt secret value for User."""
    # Sample: auth = "ldap"
    cmd = f"salt-call lyveutil.decrypt {auth_key} {secret}"
    response = list(run_subprocess_cmd(cmd))

    if response[0] == 127:
        message = str(DECRYPT_PASSWD_CMD_ERROR)
        logger.error(f"decrypt_secret: {cmd} resulted in {message} ")
    elif response[0] == 0:
        res = json.loads(response[1])
        res = res['local']
        if not res:
            message = f"decrypt_secret: Could not decrypt secret data: {secret}"
            response[2] = f"Could not decrypt secret data: {secret}"
            response[0] = 1
            logger.error(f"decrypt_secret: {cmd} resulted in {message} ")
        else:
            response[1] = res
            message = f"decrypt_secret data {res}"
            logger.debug(f"decrypt_secret: {cmd} resulted in {message} ")
    else:
        message = str(DECRYPT_PASSWD_FAILED)
        logger.error(f"decrypt_secret: {cmd} resulted in {message} ")

    return {"ret_code": response[0],
            "response": response[1],
            "error_msg": response[2],
            "message": message}