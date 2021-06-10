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
# Cortx Setup API to add storage enclosures to storagesets


from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx_setup.commands.common_utils import (
    get_cluster_id,
    get_pillar_data
)

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx.utils.conf_store import Conf


class AddStorageEnclosure(Command):
    _args = {
        'storage_set_name': {
            'type': str,
            'default': 'storage-set-1',
            'optional': False,
            'help': 'Storageset name'
        },
        'storage_enclosure': {
            'type': str,
            'nargs': '+',
            'optional': False,
            'help': 'List of storage enclosure(s) to be added to storageset'
        }
    }

    def run(self, storage_set_name=None, storage_enclosure=None):
        try:
            node_id = local_minion_id()
            index = 'storageset_index'

            Conf.load(
                index,
                f'json://{CONFSTORE_CLUSTER_FILE}'
            )
            cluster_id = get_cluster_id()

            ss_name = Conf.get(index, f'cluster>{cluster_id}>storage_set[0]>name')
            node_count = get_pillar_data("cluster/storage_set/count")

            if ss_name != storage_set_name:
                raise Exception(
                   "Invalid Storageset name provided: "
                   f"'{storage_set_name}' not found in ConfStore data. "
                   "First, set with `cortx_setup storageset create` command."
                )

            # TODO: This is Placeholder. Exact API not provided yet.
            # Addnl validation needed. Change `storage_enclosure` from list
            # to string and allow only one enclosure to be updated at a time?

            input_nodes_count = len(storage_enclosure)
            if input_nodes_count > node_count:
                raise ValueError(
                   f"Invalid count: {input_nodes_count} number of nodes received. "
                   f"Given Storageset can accept a maximum of {node_count} enclosures. "
                   "Update node count with `cortx_setup storageset create` command."
                )

            self.logger.debug(
                "Adding '{storage_enclosure}' to storageset "
                f"'{storage_set_name}' in ConfStore."
            )

            PillarSet().run(
                'cluster/storage_set/storage_enclosures',
                storage_enclosure,
                local=True
            )
            Conf.set(
                index,
                f'cluster>{cluster_id}>storage_set[0]>storage_enclosures',
                storage_enclosure
            )

            Conf.save(index)
            self.logger.debug(f"Storage enclosure '{storage_enclosure}' added.")

        except ValueError as exc:
            raise ValueError(
              f"Failed to add storage enclosure to storageset. Reason: {str(exc)}"
            )
