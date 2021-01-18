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

# How to test:
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call setup_conf.conf_cmd "../files/samples/setup.yaml"
#   'test:post_install'

import errno
import logging
import os
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

    logger.debug(f"Setup config file {conf_file}")

    replacement_url = __pillar__['provisioner']['common_config']['url']
    ret_val = ''
    with open(conf_file, 'r') as fd:
        try:
            yml_dict = yaml.safe_load(fd)

            # This split is hard-coded as this is the input format expected
            # during call from the sls file.
            root_node = conf_key.split(':')[0]
            config_stage = conf_key.split(':')[1]
            cmd_path = yml_dict[root_node][config_stage]['cmd']
            logger.debug(f"The command path from yaml file: {cmd_path}")

            # Proceed to process args, only if command has been specified
            if cmd_path and os.path.exists(cmd_path):
                args = yml_dict[root_node][config_stage]['args']

                # If args is a string, do nothing.
                # If args is a list, join the elements into a string
                if isinstance(args, list):
                    args = ' '.join(args)
                    args.replace("$URL", replacement_url)
                    logger.debug(f"Arguments for command {cmd_path}: {args}")

                ret_val = cmd_path + " " + str(args)
                logger.debug(f"{ret_val}")

        except yaml.YAMLError as ymlerr:
            # Oops, yaml file was not well formed
            logger.debug(f"Error parsing yaml file {conf_file}:\n {ymlerr}")
            ret_val = None

    return ret_val
