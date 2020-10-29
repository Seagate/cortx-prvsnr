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

def check_subprocess_output(cmd, **kwargs):
    _kwargs = dict(
        universal_newlines=True,
        stderr=subprocess.PIPE,
        shell=True,
    )

    _kwargs.update(kwargs)

    try:
        logger.debug(f"Command: {cmd}, kwargs: {_kwargs}")
        res = subprocess.check_output(cmd, **_kwargs)
        if not isinstance(res, str):
            res.decode("utf-8")
        result = (0, res, '')
        logger.debug(f"Output: {result}")
    except Exception as exc:
        result = (1, str(exc), repr(exc))
        logger.error(f"Exception: {result}")
    return result

def ssh_remote_machine(hostname, port=22, username=None, password=None):
    """ SSH Remote Execution.
    """
    logger.info("SSH Remote Execution")
    ssh_client = paramiko.client.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    response = {}
    try:
        ssh_client.connect(hostname, port, username, password)
        response['ret_code'] = 0
        response['response'] = str(SSH_CONN_CHECK)
        response['error_msg'] = "NULL"
        response['message'] = str(SSH_CONN_CHECK)
        logger.debug(response)
    except Exception as exc:
        response['ret_code'] = 1
        response['response'] = str(exc)
        response['error_msg'] = repr(exc)
        response['message'] = str(SSH_CONN_ERROR)
        logger.error(response)

    ssh_client.close()
    return response

def decrypt_secret(enc_key, secret):
    """ Decrypt secret value for User.
    """
    response = {}
    logger.info("Decrypt secret value for User")
    # Sample: enc_key = "ldap" or "cluster"
    cmd = f"salt-call lyveutil.decrypt {enc_key} {secret} --output=newline_values_only"
    res = run_subprocess_cmd(cmd)

    response['ret_code'] = res[0]
    response['response'] = res[1]
    response['error_msg'] = res[2]

    if response['ret_code'] == 127:
        message = str(DECRYPT_PASSWD_CMD_ERROR)
        logger.error(f"Command: '{cmd}' Output '{message}'")

    elif response['ret_code'] == 0:
        response['response'] = res[1].strip()
        if not response['response']:
            message = str(DECRYPT_SECRET_ERROR).format(secret)
            response['ret_code'] = 1
            logger.error(f"Command: '{cmd}' Output '{message}'")
        else:
            message = str(DECRYPT_SECRET_SUCCESS).format(response['response'])
            logger.debug(f"Command: '{cmd}' Output '{message}'")

    else:
        message = str(DECRYPT_PASSWD_FAILED)
        logger.error(f"decrypt_secret: {cmd} resulted in {message} ")

    response['message'] = message

    return response
