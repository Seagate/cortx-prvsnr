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
import os
import subprocess
import yaml

from pathlib import Path

logger = logging.getLogger(__name__)


def sync_files(component="provisioner"):
    """
    Synchronize the files as-is across nodes based on the list of files
    in the section <component>:sync:files in setup.yaml within
    component directory (/opt/seagate/<component>/conf/setup.yaml).

    The location of file on source node shall be the same on the
    destination node.
    E.g. /var/lib/seagate/provisioner/provisioner_custom_config.conf
    on srvnode-1 shall be copied to
    /var/lib/seagate/provisioner/provisioner_custom_config.conf
    on srvnode-2.
    """
    yaml_file = Path(f'/opt/seagate/cortx/{component}/conf/setup.yaml')
    if not yaml_file.exists():
        logger.exception("ERROR: {0} doesn't exist.".format(yaml_file))
        return False

    # This generic logic should always work
    node_list = __pillar__["cluster"]["node_list"]
    node_list.remove(__grains__["id"])
    node = node_list[0]

    with open(yaml_file, 'r') as fd:
        yaml_dict = yaml.safe_load(fd)

        if (
            "backup" in yaml_dict[component]
            and "files" in yaml_dict[component]["backup"]
        ):
            cmd_args = "rsync --archive --compress --update"
            for file in yaml_dict[component]["backup"]["files"]:
                dst = Path, Path(file).parent
                cmd = [f"{cmd_args} {file} {node}:{dst}"]
                proc_completed = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                try:
                    proc_completed.check_returncode()
                    logger.info("Command exited with retcode: 0 ")
                    logger.info(f"stdout: {proc_completed.stdout}")
                except subprocess.CalledProcessError:
                    logger.error(f"Command: {' '.join(cmd)}")
                    logger.error(f"Error: {proc_completed.stderr}")
                    raise Exception(proc_completed.stderr)
    return True


def backup_files(component="provisioner"):
    """
    Back the files as-is from best available live node
    based on the list of files in the section <component>:backup:files
    in setup.yaml within component directory
    (/opt/seagate/<component>/conf/setup.yaml).

    The location of file on source node shall be the appended
    with source node name directory on the destination node.
    E.g. /var/lib/provisioner_custom_config.conf
    on srvnode-1 shall be copied to
    /var/lib/srvnode-1/provisioner/provisioner_custom_config.conf
    on srvnode-2.
    """

    yaml_file = Path(f'/opt/seagate/cortx/{component}/conf/setup.yaml')
    if not yaml_file.exists():
        msg = f"ERROR: {yaml_file} doesn't exist."
        # raise Exception(msg)
        logger.exception(msg)
        return False

    # This generic logic should always work
    current_node = __grains__["id"]
    node_list = __pillar__["cluster"]["node_list"]
    node_list.remove(current_node)
    node = node_list[0]

    with open(yaml_file, 'r') as fd:
        yaml_dict = yaml.safe_load(fd)

        if (
            "backup" in yaml_dict[component]
            and "files" in yaml_dict[component]["backup"]
        ):
            cmd_args = f"rsync --archive --compress --exclude '{node}'"

            for file in yaml_dict[component]["backup"]["files"]:
                file_path = Path(file)
                if not file_path.exists():
                    continue

                dst = file_path.parent.joinpath(current_node)
                cmd = [f"{cmd_args} {file_path} {node}:{dst}{os.sep}"]
                # cmd = [f"{cmd} {file_path.parent} {node}:{dst}"]

                # For pathlib: https://bugs.python.org/issue21039
                proc_completed = subprocess.run(
                    cmd,
                    # shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                try:
                    proc_completed.check_returncode()
                    logger.info("Command exited with retcode: 0 ")
                    logger.info(f"stdout: {proc_completed.stdout}")
                except subprocess.CalledProcessError:
                    logger.error(f"Command: {' '.join(cmd)}")
                    logger.error(f"Error: {proc_completed.stderr}")
                    raise Exception(proc_completed.stderr)

    return True


def restore_files(component="provisioner"):
    """
    Restore the files as-is across nodes based on the list of files
    in the section <component>:sync:files in setup.yaml within
    component directory (/opt/seagate/<component>/conf/setup.yaml).

    The location of file on source node shall be the appended
    with source node name directory on the destination node.
    E.g. /var/lib/seagate/provisioner/provisioner_custom_config.conf
    on srvnode-1 shall be copied to
    /var/lib/seagate/provisioner/srvnode-1/provisioner_custom_config.conf
    on srvnode-2.
    """

    yaml_file = Path(f'/opt/seagate/cortx/{component}/conf/setup.yaml')
    if not yaml_file.exists():
        msg = f"ERROR: {yaml_file} doesn't exist."
        # raise Exception(msg)
        logger.exception(msg)
        return False

    # Execute on replacement_node only
    replacement_node = None
    if __pillar__["cluster"]["replace_node"]["minion_id"]:
        replacement_node = __pillar__["cluster"]["replace_node"]["minion_id"]
    elif os.getenv("NODE_REPLACED", False):
        replacement_node = os.getenv("REPLACEMENT_NODE", False)
    else:
        replacement_node = None

    # Execute only if replacement_node is set
    # and is the current node is replacement node
    if (
        replacement_node and
        __grains__["id"] == replacement_node
    ):
        node_list = __pillar__["cluster"]["node_list"]
        node_list.remove(replacement_node)
        node = node_list[0]

        with open(yaml_file, 'r') as fd:
            yaml_dict = yaml.safe_load(fd)

            if (
                "backup" in yaml_dict[component] and
                "files" in yaml_dict[component]["backup"]
            ):
                cmd_args = "rsync --archive --compress"

                for file in yaml_dict[component]["backup"]["files"]:
                    file_path = Path(file)
                    src = file_path.parent.joinpath(
                        replacement_node,
                        file_path
                    )
                    dst = file_path.parent
                    cmd = [f"{cmd_args} {node}:{src}{os.sep} {dst}{os.sep}"]

                    proc_completed = subprocess.run(
                            cmd,
                            # shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                    )

                    try:
                        proc_completed.check_returncode()
                        logger.info("Command exited with retcode: 0 ")
                        logger.info(f"stdout: {proc_completed.stdout}")
                    except subprocess.CalledProcessError:
                        logger.error(f"Command: {' '.join(cmd)}")
                        logger.error(f"Error: {proc_completed.stderr}")
                        raise Exception(proc_completed.stderr)
    else:
        logger.warning(
            f"WARN: replacement_node is {replacement_node} "
            f"and doesn't match the current execution node {__grains__['id']}"
        )
        return False

    return True
