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
        msg = f"ERROR: {str(yaml_file)} doesn't exist."
        # raise Exception(msg)
        logger.error(msg)
        return False

    # This generic logic should always work
    node_list = __pillar__["cluster"]["node_list"]
    node_list.remove(__grains__["id"])
    node = node_list[0]

    yaml_dict = yaml.safe_load(yaml_file.read_text())

    if (
        "backup" in yaml_dict[component]
        and "files" in yaml_dict[component]["backup"]
    ):
        cmd_args = ["/usr/bin/rsync", "--archive", "--compress", "--update"]
        for file in yaml_dict[component]["backup"]["files"]:
            file_path = Path(file)
            if not file_path.exists():
                msg = (
                    f"File {str(file_path)} mentioned in yaml_file, "
                    "does not exist."
                )
                logger.warning(msg)
                continue

            dst = Path(file_path).parent
            cmd = (
                cmd_args
                + [file_path, f"{node}:{dst}"]
            )

            proc_completed = subprocess.run(
                [f"{' '.join(cmd)}"],
                # shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                proc_completed.check_returncode()
                msg = (
                    "Command exited with retcode: 0 "
                    f"stdout: {proc_completed.stdout}"
                )
                logger.debug(msg)
            except subprocess.CalledProcessError:
                msg = (
                        f"Command: {' '.join(cmd)} "
                        f"Error: {proc_completed.stderr}"
                    )
                logger.error(msg)
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
        msg = f"ERROR: {str(yaml_file)} doesn't exist."
        # raise Exception(msg)
        logger.error(msg)
        return False

    # This generic logic should always work
    current_node = __grains__["id"]
    node_list = __pillar__["cluster"]["node_list"]
    node_list.remove(current_node)
    node = node_list[0]

    yaml_dict = yaml.safe_load(yaml_file.read_text())

    if (
        "backup" in yaml_dict[component]
        and "files" in yaml_dict[component]["backup"]
    ):
        cmd_args = [
                    "/usr/bin/rsync", "--archive", "--compress",
                    "--exclude", f"{node}"
                ]

        for file in yaml_dict[component]["backup"]["files"]:
            file_path = Path(file)
            if not file_path.exists():
                msg = (
                    f"File {str(file_path)} mentioned in yaml_file, "
                    "does not exist."
                )
                logger.warning(msg)
                continue

            dst = file_path.parent.joinpath(current_node)

            cmd = (
                cmd_args
                + [str(file_path), f"{node}:{dst}{os.sep}"]
            )

            # For pathlib: https://bugs.python.org/issue21039
            proc_completed = subprocess.run(
                [f"{' '.join(cmd)}"],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                proc_completed.check_returncode()
                msg = (
                    "Command exited with retcode: 0 "
                    f"stdout: {proc_completed.stdout}"
                )
                logger.debug(msg)
            except subprocess.CalledProcessError:
                msg = (
                    f"Command: {' '.join(cmd)} "
                    f"Error: {proc_completed.stderr}"
                )
                logger.error(msg)
                raise Exception(proc_completed.stderr)

    return True


def restore_files(component="provisioner"):
    """
    Restore the files as-is across nodes.

    This is based on the list of files in the section
    <component>:sync:files in setup.yaml within
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
        msg = f"ERROR: {str(yaml_file)} doesn't exist."
        # raise Exception(msg)
        logger.error(msg)
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
    if not (
        replacement_node and
        __grains__["id"] != replacement_node
    ):
        logger.warning(
            f"Replacement_node is {replacement_node} "
            f"and it's the same current execution node {__grains__['id']}"
        )
        return False

    # node_list = __pillar__["cluster"]["node_list"]
    # node_list.remove(replacement_node)
    # node = node_list[0]

    yaml_dict = yaml.safe_load(yaml_file.read_text())

    if (
        "backup" in yaml_dict[component] and
        "files" in yaml_dict[component]["backup"]
    ):
        cmd_args = ["/usr/bin/rsync", "--archive", "--compress"]

        for file in yaml_dict[component]["backup"]["files"]:
            file_path = Path(file)
            src = file_path.parent.joinpath(
                replacement_node,
                file_path
            )
            if not src.exists():
                msg = f"Specified file ({src}) doesn't exist for restore. "
                "Skipping..."
                logger.error(msg)
                continue

            dst = file_path.parent
            cmd = (
                cmd_args
                + [f"{src}", f"{replacement_node}:{dst}{os.sep}"]
            )
            proc_completed = subprocess.run(
                    [f"{' '.join(cmd)}"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
            )

            try:
                proc_completed.check_returncode()
                msg = (
                    "Command exited with retcode: 0 "
                    f"stdout: {proc_completed.stdout}"
                )
                logger.debug(msg)
            except subprocess.CalledProcessError:
                msg = (
                    f"Command: {' '.join(cmd)} "
                    f"Error: {proc_completed.stderr}"
                )
                logger.error(msg)
                raise Exception(proc_completed.stderr)

    return True
