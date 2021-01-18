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
#   "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/setup.yaml"
#   "test:post_install"

import errno
import logging
import os
import subprocess
import yaml


logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


def conf_cmd(conf_file, conf_key):
    if not os.path.exists(conf_file):
        logger.error(f"Setup config file {conf_file} doesn't exist.")
        raise FileNotFoundError(
          errno.ENOENT,
          os.strerror(errno.ENOENT),
          conf_file
        )

    logger.debug(f"Setup config file: {conf_file}")

    confstore_url = __pillar__['provisioner']['common_config']['url']
    ret_val = ''
    with open(conf_file, 'r') as fd:
        try:
            config_info = yaml.safe_load(fd)

            # This split is hard-coded as this is the input format expected
            # during call from the sls file.
            component_setup = config_info[conf_key.split(':')[0]]
            component_interface = component_setup[conf_key.split(':')[1]]
            interface_cmd = component_interface['cmd']
            logger.debug(
                "For component interface "
                f"'{conf_key.split(':')[0]}:{conf_key.split(':')[1]}' "
                f"command: {interface_cmd}"
            )

            # Check if command exists
            try:
                subprocess.check_call(
                    f"{interface_cmd} --help",
                    stdout=subprocess.DEVNULL,
                    shell=True
                )
            except FileNotFoundError as fnf_err:
                logger.exception(fnf_err)
            except subprocess.CalledProcessError as cp_err:
                logger.exception(cp_err)

            # Proceed to process args, only if command has been specified
            if interface_cmd:
                interface_cmd_args = component_interface['args']

                # If args is a string, do nothing.
                # If args is a list, join the elements into a string
                if isinstance(interface_cmd_args, list):
                    interface_cmd_args = ' '.join(interface_cmd_args)
                    interface_cmd_args = interface_cmd_args.replace(
                        "$URL",
                        confstore_url
                    )
                    logger.debug(
                        f"Arguments for command {interface_cmd}: "
                        f"{interface_cmd_args}"
                    )

                ret_val = interface_cmd + " " + str(interface_cmd_args)
                logger.debug(f"Command formed for execution: {ret_val}")

        except yaml.YAMLError as yml_err:
            # Oops, yaml file was not well formed
            logger.debug(
                f"Error parsing component setup config - {conf_file}: "
                f"{yml_err}"
            )
            ret_val = None

    logger.info(f"Component setup command: {ret_val}")
    return ret_val
