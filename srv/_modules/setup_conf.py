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
import logging
import os
import sys
import yaml

from subprocess import (
    run,
    CalledProcessError,
    DEVNULL
)

logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

risky_commands = [
    'rm',
    'yum',
    'erase',
    'uninstall'
]


def conf_cmd(conf_file, conf_key):
    if not os.path.exists(conf_file):
        logger.error(f"Setup config file {conf_file} doesn't exist.")
        raise FileNotFoundError(
        errno.ENOENT,
        os.strerror(errno.ENOENT),
        conf_file
        )

    logger.debug(f"Setup config file: {conf_file}")

    __pillar__ = getattr(sys.modules[__name__], '__pillar__')
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
                raise Exception(f"Execution of command {setup_cmd} is identified "
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
                run(
                    cmd_as_list,
                    stdout=DEVNULL,
                    check=True
                )
            except CalledProcessError as cp_err:
                logger.exception(f"Command {' '.join(cmd_as_list)} "
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
