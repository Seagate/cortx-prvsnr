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
import yaml
import subprocess
import logging

from pathlib import Path

__virtualname__ = 'setup_conf'

try:
    import provisioner
except ImportError:
    # TODO pip3 installs provisioner to /usr/local/lib/python3.6/site-packages
    #      but that directory is not listed in salt's sys.path,
    #      EOS-5401 might be related
    try:
        prvsnr_pkg_path = subprocess.run(
            "python3 -c 'import provisioner; print(provisioner.__file__)'",
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True
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


def _call_cmd(cmd):
    # TODO provide env according to spec
    __salt__ = _salt_salt()
    return __salt__["cmd.run"](cmd, output_loglevel="trace", python_shell=True)


class ConfSetupHelper:

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


def hook(
    hook,
    flow,
    level,
    sw=None,
    fail_fast=False
):
    helper = ConfSetupHelper(_salt_pillar())

    if sw is None:
        sw_list = list(helper.sw_data)
    else:
        sw_list = [sw]

    excs = []
    for sw in sw_list:
        try:
            setup_spec = helper.sw_spec(sw, flow, level)
            cmd = setup_spec.get(hook)
            # assuming that normailized spec2 includes only active hooks
            # with commands as values
            if cmd:
                res = _call_cmd(cmd)
                logger.debug(
                    f"Hook '{hook}' command '{cmd}'"
                    f" for '{sw}' resulted in: {res}"
                )
        except Exception as exc:
            logger.warning(
                f"Hook '{hook}' command '{cmd}' for '{sw}' failed: {exc}"
            )
            if fail_fast:
                raise
            else:
                excs.append((sw, hook, cmd, exc))

    if excs:
        raise ProvisionerError(str(excs))


def raise_event(event, flow, level, fail_fast=False):
    ev_field = MiniAPISpecFields.EVENTS.value

    helper = ConfSetupHelper(_salt_pillar())

    events = []
    for sw in helper.sw_data:
        setup_spec = helper.sw_spec(sw, flow, level)
        # assuming that normailized spec includes only active hooks
        # with commands as values
        if setup_spec and event in setup_spec[ev_field]:
            events.append((sw, setup_spec[ev_field][event]))

    excs = []
    for sw, cmd in events:
        try:
            res = _call_cmd(cmd)
            logger.warning(
                f"Event '{event}' command '{cmd}' "
                f"for '{sw}' resulted in: {res}"
            )
        except Exception as exc:
            logger.warning(
                f"Event '{event}' command '{cmd}' for '{sw}' failed: {exc}"
            )
            if fail_fast:
                raise
            else:
                excs.append((sw, event, cmd, exc))

    if excs:
        raise ProvisionerError(str(excs))


def conf_cmd(conf_file, conf_key):
    if not os.path.exists(conf_file):
        logger.error(f"Setup config file {conf_file} doesn't exist.")
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            conf_file
        )

    logger.debug(f"Setup config file: {conf_file}")

    __pillar__ = _salt_pillar()
    confstore_url = __pillar__['provisioner']['common_config']['confstore_url']
    ret_val = ''
    with open(conf_file, 'r') as fd:
        try:
            config_info = yaml.safe_load(fd)

            # This split is hard-coded as this is the input format expected
            # during call from the sls file.
            component_setup = config_info[conf_key.split(':')[0]]
            component_interface = component_setup[conf_key.split(':')[1]]
            setup_cmd = component_interface['cmd']
            logger.debug(
                f"Component Setup Command: {setup_cmd}"
            )

            if set(risky_commands).intersection(setup_cmd.split()):
                raise Exception(
                    f"Execution of command {setup_cmd} is identified "
                    "as a command with risky behavior. "
                    f"Hence, execution of command {setup_cmd} is prohibited."
                )

            # Check if command exists
            try:
                # The command string has to be converted to a list
                # to enabled execution of check_call with shell=False
                cmd_as_list = (f"{setup_cmd} --help").split()
                logger.debug(
                    f"Component setup command as list: {cmd_as_list}"
                )
                subprocess.run(
                    cmd_as_list,
                    stdout=subprocess.DEVNULL,
                    check=True
                    # env=env EOS-20788 POC
                )
            except subprocess.CalledProcessError as cp_err:
                logger.exception(
                    f"Command {' '.join(cmd_as_list)} "
                    f"returned with error: {cp_err.stderr}"
                )
            except FileNotFoundError as fnf_err:
                logger.exception(fnf_err)

            # Proceed to process args, only if command has been specified
            if setup_cmd:
                setup_args = component_interface['args']

                # If args is a string, do nothing.
                # If args is a list, join the elements into a string
                if isinstance(setup_args, list):
                    setup_args = ' '.join(setup_args)
                    logger.debug(
                        f"Component Setup Command Args: {setup_args}"
                    )

                setup_args = setup_args.replace(
                    "$URL",
                    confstore_url
                )
                ret_val = setup_cmd + " " + str(setup_args)
                logger.debug(f"Component Setup: {ret_val}")

        except yaml.YAMLError as yml_err:
            # Oops, yaml file was not well formed
            logger.debug(
                f"Error parsing component setup config - {conf_file}: "
                f"{yml_err}"
            )
            ret_val = None

    logger.info(f"Component Setup: {ret_val}")
    return ret_val
