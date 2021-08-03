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
# Cortx Setup API to configure durability of a storageset


from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx_setup.commands.common_utils import (
    get_cluster_id
)

from provisioner.commands import PillarSet
from provisioner.config import (
    CONFSTORE_ROOT_FILE,
    ALL_MINIONS
)
from provisioner.salt import (
    StateFunExecuter,
    copy_to_file_roots
)
from cortx.utils.conf_store import Conf


class DurabilityConfig(Command):
    _args = {
        'storage_set_name': {
            'type': str,
            'optional': False,
            'help': 'Storageset name'
        },
        'type': {
            'type': str,
            'default': None,
            'optional': True,
            'dest': 'durability_type',
            'choices': ['sns', 'dix'],
            'help': 'Storageset durability type. e.g: {sns|dix}'
        },
        'data': {
            'type': int,
            'default': None,
            'optional': True,
            'help': 'Storageset durability data'
        },
        'parity': {
            'type': int,
            'default': None,
            'optional': True,
            'help': 'Storageset durability parity value'
        },
        'spare': {
            'type': int,
            'default': None,
            'optional': True,
            'help': 'Storageset durability spare'
        }
    }

    def run(self, **kwargs):
        try:
            confstore_config = 'storage_durability_index'
            storage_set_name = kwargs['storage_set_name']
            durability_type = kwargs['durability_type']

            if None in [durability_type, kwargs['data'], kwargs['parity'], kwargs['spare']]:
                raise Exception(
                    "ERROR: Insufficient command parameters type specified")

            cluster_id = get_cluster_id()
            durability_dict = {
                'data': str(kwargs['data']),
                'parity': str(kwargs['parity']),
                'spare': str(kwargs['spare'])
            }

            self.load_conf_store(
                confstore_config,
                f'json://{CONFSTORE_CLUSTER_FILE}'
            )

            storage_set_info = Conf.get(
                confstore_config, f'cluster>{cluster_id}>storage_set')
            storage_set_index = -1

            for index, _ in enumerate(storage_set_info):
                if storage_set_info[index]['name'] == storage_set_name:
                    storage_set_index = index
                    break

            if storage_set_index == -1:
                raise ValueError(
                    f"Error: Storage-set '{storage_set_name}' not found."
                    "Action: Configure with 'cortx_setup storageset create' command"
                )

            confstore_durability_key = f'cluster>{cluster_id}>storage_set[{storage_set_index}]>durability'
            pillar_durability_key = 'cluster/srvnode-1/storage/durability'

            PillarSet().run(
                f'{pillar_durability_key}/{durability_type}',
                durability_dict
            )
            Conf.set(
                confstore_config,
                f'{confstore_durability_key}>{durability_type}',
                durability_dict
            )
            Conf.save(confstore_config)
            self.logger.debug(
                f"Durability configured for Storageset '{storage_set_name}'"
            )

            # Copy the current confstore across all nodes
            dest = copy_to_file_roots(
                CONFSTORE_CLUSTER_FILE, CONFSTORE_ROOT_FILE)
            self.logger.debug("Confstore file provisioner root directory")

            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=str(CONFSTORE_CLUSTER_FILE),
                    source=str(dest),
                    makedirs=True
                ),
                targets=ALL_MINIONS
            )
            self.logger.debug("Confstore copied across all nodes of cluster")

        except ValueError as exc:
            raise ValueError(
                f"Failed to configure durability. Reason: {str(exc)}"
            )
