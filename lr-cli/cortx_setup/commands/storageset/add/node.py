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
#
# Cortx Setup API to add server nodes to storagesets


from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx_setup.commands.common_utils import (
    get_cluster_id,
    get_machine_id,
    get_pillar_data
)

from provisioner.commands import PillarSet
from cortx.utils.conf_store import Conf


class AddServerNode(Command):
    _args = {
        'storage_set_name': {
            'type': str,
            'default': 'storage-set-1',
            'optional': False,
            'help': 'Storageset name'
        },
        'server_node': {
            'type': str,
            'nargs': '+',
            'optional': False,
            'help': ('List of server node(s) space-separated to be added '
                     'to storageset. e.g. srvnode-1 srvnode-2')
        }
    }

    def run(self, storage_set_name=None, server_node=None):
        try:
            index = 'storage_add_index'
            cluster_id = get_cluster_id()
            machine_id = []

            self.load_conf_store(
                index,
                f'json://{CONFSTORE_CLUSTER_FILE}'
            )

            try:
                storageset = Conf.get (
                    index,
                    f'cluster>{cluster_id}>storage_set'
                )
                storage_set_len = len(storageset)
            except Exception:
                self.logger.debug(
                    "No storage-set found, setting storage_set_len to 0"
                )
                storage_set_len = 0

            if storage_set_len == 0:
                self.logger.debug(
                    "storage-set object is empty"
                )
                raise Exception(
                   f"Error: Storage-set {storage_set_name} does not exist."
                   " Use command - cortx_setup storageset create"
                )

            ss_found = False
            for ss_index in range(0, storage_set_len):
                ss_name = Conf.get(
                    index, f'cluster>{cluster_id}>storage_set[{ss_index}]>name'
                )
                if ss_name == storage_set_name:
                    ss_found = True
                else:
                    continue

            if ss_found == False:
                self.logger.debug(
                    f"Cannot find storage-set: {storage_set_name}"
                )
                raise Exception(
                   f"Error: Storage-set {storage_set_name} does not exist."
                   " Use command - cortx_setup storageset create"
                )

            node_count = get_pillar_data("cluster/storage_set/count")

            # TODO: Addnl validation needed. Change server_node from list
            # to string and allow only one node to be updated at a time?

            input_nodes_count = len(server_node)

            if input_nodes_count > node_count:
                raise ValueError(
                   f"Invalid count: {input_nodes_count} number of nodes received. "
                   f"Given Storageset can accept a maximum of {node_count} nodes. "
                   "Update it with `cortx_setup storageset create` command."
                )

            # Get corresponding machine-id of each node
            for node in server_node:
                machine_id.append(get_machine_id(node))

            self.logger.debug(
                f"Adding machine_id '{machine_id}' to storage-set "
                f"'{storage_set_name}' in ConfStore."
            )

            PillarSet().run(
                'cluster/storage_set/server_nodes',
                machine_id
            )
            Conf.set(
                index,
                f'cluster>{cluster_id}>storage_set[{ss_index}]>server_nodes',
                machine_id
            )

            for node in server_node:
                machine_id = get_machine_id(node)
                self.logger.debug(
                    f"Adding storage set ID:{storage_set_name} to "
                    f"server {node} with machine id: {machine_id}"
                )
                Conf.set(
                    index,
                    f'server_node>{machine_id}>storage_set_id',
                    storage_set_name
                )

            Conf.save(index)
            self.logger.debug(f"Server nodes {server_node} with correspoding "
                              f"machine_ids added to Storageset")

        except ValueError as exc:
            raise ValueError(
              f"Failed to add node to storageset. Reason: {str(exc)}"
            )
