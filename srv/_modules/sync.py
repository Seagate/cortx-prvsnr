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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

import logging
import os
import subprocess
import yaml

from pathlib import PurePath

logger = logging.getLogger(__name__)

def sync_files(component="provisioner", replace_node=False):
    
    yaml_file = f'/opt/seagate/cortx/{component}/conf/setup.yaml'
    if not os.path.exists(yaml_file):
        logger.exception("ERROR: {0} doesn't exist.".format(yaml_file))
        return False

    replace_node = None
    if __pillar__["cluster"]["replace_node"]["minion_id"]:
        replace_node = __pillar__["cluster"]["replace_node"]["minion_id"]
    elif os.getenv("NODE_REPLACED", False):
        replace_node = os.getenv("REPLACEMENT_NODE", False)
    else:
        replace_node = None

    node = __grains__["id"]
    # if not replace_node:
    #     if node == "srvnode-1":
    #         node = "srvnode-2"
    #     else:
    #         node = "srvnode-1"
    # else:
    #     node_list = __pillar__["cluster"]["node_list"]
    #     node_list.remove(node)
    #     node = node_list[0]

    # This generic logic should always work
    node_list = __pillar__["cluster"]["node_list"]
    node_list.remove(node)
    node = node_list[0]

    with open(yaml_file, 'r') as fd:
        yaml_dict = yaml.safe_load(fd)

        if "backup" in yaml_dict[component] and "files" in yaml_dict[component]["backup"]:
            cmd = "rsync -zavhe ssh"
            for file in yaml_dict[component]["backup"]["files"]:
                dst = PurePath(file).parent
                logger.info(
                    subprocess.run(
                        [f"{cmd} {node}:{file} {dst}"],
                        shell = True,
                        stdout = subprocess.PIPE
                )
            )
    return True

