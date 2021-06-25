# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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

# How to test:
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call setup_conf.conf_cmd
#   conf_file="/opt/seagate/cortx/provisioner/srv/_modules/files/samples/setup.yaml"
#   conf_key="test:post_install"

import errno
import os
import sys
import subprocess
import logging

from pathlib import Path

__virtualname__ = 'setup_conf'

try:
    import provisioner  # pylint: disable=unused-import
except ImportError:
    # TODO pip3 installs provisioner to /usr/local/lib/python3.6/site-packages
    #      but that directory is not listed in salt's sys.path,
    #      EOS-5401 might be related
    try:
        prvsnr_pkg_path = subprocess.run(  # nosec
            [
                "python3", "-c",
                "import provisioner; print(provisioner.__file__)"
            ],
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True
        ).stdout.strip()
        sys.path.insert(0, str(Path(prvsnr_pkg_path).parent.parent))
        import provisioner  # noqa: F401
    except Exception:
        HAS_PROVISIONER = False
    else:
        HAS_PROVISIONER = True
else:
    HAS_PROVISIONER = True


if HAS_PROVISIONER:
    from provisioner.commands.mini_api import SpecRenderer
    from provisioner.config import MiniAPISpecFields
    from provisioner.errors import ProvisionerError


def __virtual__():  # noqa: N807
    if HAS_PROVISIONER:
        return __virtualname__
    else:
        return (
            False,
            (
                "The 'setup_conf' execution module cannot be loaded:"
                " provisioner package unavailable."
            )
        )


# logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

risky_commands = [
    'rm',
    'yum',
    'erase',
    'uninstall'
]


def _salt_builtin(name):
    return getattr(sys.modules[__name__], name)


def _salt_pillar():
    return _salt_builtin('__pillar__')


def _salt_salt():
    return _salt_builtin('__salt__')


def _call_cmd(cmd, env=None):
    if isinstance(cmd, (list, tuple)):
        cmd = ' '.join(cmd)

    logger.debug(
        f"'{cmd}' command would be called"
    )

    __salt__ = _salt_salt()
    return __salt__["cmd.run"](
        cmd, output_loglevel="trace", python_shell=True, env=env
    )


class ConfSetupHelper:

    @staticmethod
    def env(hook, flow, level, ctx_vars=None):
        res = ctx_vars or {}
        res.update(dict(
            PRVSNR_MINI_HOOK=hook,
            PRVSNR_MINI_FLOW=flow,
            PRVSNR_MINI_LEVEL=level
        ))
        return res

    def __init__(self, pillar, salt=None):
        self.pillar = pillar
        self.salt = salt

    @property
    def sw_data(self):
        return self.pillar['commons']['sw_data']

    @property
    def confstore_url(self):
        return self.pillar['provisioner']['common_config']['confstore_url']

    def sw_spec(self, sw, flow, level):
        conf_path = self.sw_data.get(sw, {}).get('mini')

        spec = {}
        if conf_path and Path(conf_path).exists():
            spec = SpecRenderer(
                conf_path,
                flow,
                level,
                confstore=self.confstore_url,
                normalize=True
            ).build().get(sw, {})

        return spec

    def filter_sw(self, sw):
        if sw is None:
            sw_list = list(self.sw_data)
        elif isinstance(sw, str):
            sw_list = sw.split()
        else:
            sw_list = sw

        diff = set(sw_list) - set(self.sw_data)
        if diff:
            logger.warning(
                f"The following unexpected SW would be ignored: '{diff}'"
            )
        # XXX ??? is it required to define the order here
        return [_sw for _sw in self.sw_data if _sw in sw_list]


def hook(
    hook,
    flow,
    level,
    sw=None,
    ctx_vars=None,
    fail_fast=False
):
    ev_field = MiniAPISpecFields.EVENTS.value

    helper = ConfSetupHelper(_salt_pillar())
    sw_list = helper.filter_sw(sw)

    excs = {}
    done = []
    for sw in sw_list:
        try:
            setup_spec = helper.sw_spec(sw, flow, level)
            cmd = (
                setup_spec.get(hook)  # base hook
                or setup_spec.get(ev_field, {}).get(hook)  # or event
            )
            # assuming that normailized spec2 includes only active hooks
            # with commands as values
            if cmd:
                res = _call_cmd(
                    cmd, env=helper.env(hook, flow, level, ctx_vars=ctx_vars)
                )
                logger.debug(
                    f"Hook '{hook}' command '{cmd}'"
                    f" for '{sw}' resulted in: '{res}'"
                )
                done.append(sw)
        except Exception as exc:
            logger.warning(
                f"Hook '{hook}' command '{cmd}' for '{sw}' failed: {exc}"
            )
            if fail_fast:
                raise
            else:
                excs[sw] = (cmd, exc)

    if excs:
        raise ProvisionerError(
            f"Hook '{hook}' calls failed for '{list(excs)}': '{excs}'"
        )

    if not done:
        logger.info(f"No listeners for hook '{hook}' found")


# TODO deprectate, use 'hook' instead
def conf_cmd(conf_file, conf_key):
    if not os.path.exists(conf_file):
        logger.error(f"Setup config file {conf_file} doesn't exist.")
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            conf_file
        )

    logger.debug(f"Setup config file: {conf_file}")

    # This split is hard-coded as this is the input format expected
    # during call from the sls file.
    sw = conf_key.split(':')[0]
    hook = conf_key.split(':')[1]

    helper = ConfSetupHelper(_salt_pillar())
    # legacy case: only base hooks for 'deploy' flow on 'node' level
    setup_spec = helper.sw_spec(sw, 'deploy', 'node')
    cmd = setup_spec.get(hook, [])

    if cmd:
        # TODO improve, some very simple check against dangerous commands
        if set(risky_commands).intersection(cmd):
            raise Exception(
                f"Execution of command '{cmd}' is identified "
                "as a command with risky behavior. "
                f"Hence, execution of command '{cmd}' is prohibited."
            )

        # Check if command exists
        try:
            # The command string has to be converted to a list
            # to enabled execution of check_call with shell=False
            help_cmd = [cmd[0], '--help']
            logger.debug(
                f"Component setup help command: {help_cmd}"
            )
            subprocess.run(  # nosec
                help_cmd,
                stdout=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError as cp_err:
            logger.exception(
                f"Command '{help_cmd}: "
                f"returned with error: {cp_err.stderr}"
            )
            # FIXME ??? legacy logic, why de don't raise exc in any case
        except FileNotFoundError as fnf_err:
            logger.exception(fnf_err)

    cmd = ' '.join(cmd)
    logger.info(
        f"Component '{sw}' Setup Command for '{hook}' hook: '{cmd}'"
    )

    return cmd
