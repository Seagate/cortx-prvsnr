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
# Cortx Setup API for adding node to Storageset in Field


from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx.utils.conf_store import Conf


class AddServerNode(Command):
    _args = {
        'storage_set_name': {
            'type': str,
            'default': 'cortx_storageset',
            'optional': False,
            'help': 'Storageset name'
        },
        'server_node': {
            'type': str,
            'nargs': '+',
            'optional': False,
            'help': 'List of Server node(s) to be added to storageset'
        }
    }

    def run(self, storage_set_name=None, server_node=None):
        node_id = local_minion_id()
        index = 'storageset_index'

        Conf.load(
            index,
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )
        ss_name = Conf.get(index, 'cluster>storage_set>name')
        node_count = Conf.get(index, 'cluster>storage_set>count')

        if not (storage_set_name and server_node):
            raise Exception(
               "Valid Storageset name and the name of server "
               "to add to it are mandatory."
            )

        if ss_name != storage_set_name:
            raise Exception(
               "Invalid Storageset name provided: "
               f"'{storage_set_name}' not found in ConfStore data. "
               "First, set with `cortx_setup storageset create` command."
            )

        if len(server_node) > node_count:
            raise Exception(
               f"Invalid count: {len(server_node)} number of nodes received. "
               f"Given Storageset can accept a maximum of {node_count} nodes. "
               "Update it with `cortx_setup storageset create` command."
            )

        self.logger.info(
            f"Adding '{server_node}' to storageset '{storage_set_name}' "
            "in ConfStore"
        )
        PillarSet().run(
            'cluster/storage_set/server_nodes',
            server_node,
            targets=node_id,
            local=True
        )
        Conf.set(
            index,
            'cluster>storage_set>server_nodes',
            server_node
        )

        Conf.save(index)
        self.logger.info("Server nodes added to Storageset")
