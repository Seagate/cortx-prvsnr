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

import sys
import os
import subprocess
import logging
from typing import List, Dict, Optional

import provisioner
from provisioner import errors
from provisioner import serialize

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


def value_to_str(v):
    if v is None:
        v = provisioner.NONE
    elif isinstance(v, (List, Dict)):
        v = serialize.dumps(v)
    return str(v)


def api_args_to_cli(fun, *args, **kwargs):
    res = [fun]
    for k, v in kwargs.items():
        k = '--{}'.format(k.replace('_', '-'))
        if type(v) is bool:
            if v:
                res.extend([k])
        else:
            res.extend([f"{k}={value_to_str(v)}"])

    res.extend([value_to_str(a) for a in args])
    logger.debug("Cli command args: {}".format(res))

    return res


# TODO tests
def process_cli_result(
    stdout: str = None, stderr: str = None
):
    res = None
    try:
        try:
            res = serialize.loads(stdout) if stdout else {}
        except errors.PrvsnrTypeDecodeError:
            logger.exception('Failed to decode provisioner output')
            res = serialize.loads(stdout, strict=False)
    except Exception:
        logger.exception(f"Unexpected result: {stdout}")

    if type(res) is not dict:
        raise errors.ProvisionerError(f'Unexpected result {stdout}')

    if 'exc' in res:
        logger.error("Provisioner CLI failed: {!r}".format(res['exc']))
        raise res['exc']
    else:
        try:
            return res['ret']
        except KeyError:
            logger.error(
                "No return data found in '{}', stderr: '{}'"
                .format(stdout, stderr)
            )
            raise errors.ProvisionerError(
                "No return data found in '{}', stderr: '{}'"
                .format(stdout, stderr)
            )


def _run_cmd(cmd, env: Optional[Dict] = None, **kwargs):
    # Note. we update a copy of current process env since
    #       subprocess.run will replace the env of the current
    #       process
    if env is not None:
        env_copy = os.environ.copy()
        env_copy.update(env)
        env = env_copy

    try:
        logger.debug("Executing command {}".format(cmd))
        res = subprocess.run(cmd, env=env, **kwargs)
    # subprocess.run fails expectedly
    except subprocess.CalledProcessError as exc:
        return process_cli_result(exc.stdout, exc.stderr)
    # subprocess.run fails unexpectedly
    except Exception as exc:
        logger.exception("Failed to execute command")
        raise errors.ProvisionerError(repr(exc)) from exc
    else:
        return process_cli_result(res.stdout, res.stderr)


# TODO test args preparation
def _api_call(fun, *args, **kwargs):
    # do not expect ad-hoc credentials here
    kwargs.pop('password', None)
    kwargs.pop('username', None)
    kwargs.pop('eauth', None)

    _input = None
    if _username and _password:
        _input = _password
        kwargs['username'] = _username
        kwargs['password'] = '-'
        kwargs['eauth'] = _eauth

    kwargs['noconsole'] = True
    kwargs['rsyslog'] = True
    kwargs['rsyslog-level'] = 'DEBUG'
    # TODO IMPROVE EOS-7495 make a config variable for formatter
    kwargs['rsyslog-formatter'] = 'full'

    cli_args = api_args_to_cli(fun, *args, **kwargs)
    cmd = ['provisioner'] + cli_args

    return _run_cmd(
        cmd,
        env={'PRVSNR_OUTPUT': 'json'},
        input=_input,
        check=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return _api_call(fun, *args, **kwargs)
    return f


def auth_init(username, password, eauth='pam'):
    global _eauth
    global _username
    global _password
    _eauth = eauth
    _username = username
    _password = password


# TODO automate commands list discovering
mod = sys.modules[__name__]
for fun in [
    'get_result',
    'pillar_get',
    'pillar_set',
    'get_params',
    'set_params',
    'set_ntp',
    'set_network',
    'set_swupdate_repo',
    'sw_update',
    'sw_rollback',
    'set_ssl_certs',
    'fw_update',
    'get_cluster_id',
    'get_node_id',
    'reboot_server',
    'reboot_controller',
    'shutdown_controller',
    'configure_cortx',
    'create_user',
    'replace_node',
    'get_release_version',
    'get_factory_version',
    'cmd_run',
    'get_setup_info',
    'show_volume_maps'
]:
    setattr(mod, fun, _api_wrapper(fun))
