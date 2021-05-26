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
# Cortx Setup API for configuring durability details for Storageset in Field


from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx.utils.conf_store import Conf


class DurabilityConfig(Command):
    _args = {
        'storage_set_name': {
            'type': str,
            'optional': False,
            'help': 'Storageset name'
        },
        'data': {
            'type': int,
            'default': None,
            'optional': True,
            'help': 'Storageset durability data'
        },
        'parity': {
            'type': int,
            'default': 1,
            'optional': True,
            'help': 'Storageset durability parity value'
        },
        'spare': {
            'type': int,
            'default': 1,
            'optional': True,
            'help': 'Storageset durability spare'
        }
    }

    def run(self, **kwargs):
        node_id = local_minion_id()
        index = 'storageset_index'

        Conf.load(
            index,
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )
        durability_type = "sns"  # Should we fetch this from Pillar?
        ss_name = Conf.get(index, 'cluster>storage_set>name')

        if ss_name != kwargs['storage_set_name']:
            raise Exception(
               "Invalid Storageset name provided: "
               f"{kwargs['storage_set_name']} not found in ConfStore data. "
               "First, set with `cortx_setup storageset create` command."
            )

#        if 'storage_set_name' not in kwargs:
#            raise Exception(
#               "Valid Storageset name is mandatory to configure durability."
#            )

        for key, value in kwargs.items():
            if value and key != 'storage_set_name':
                self.logger.info(
                    f"Updating {key} as {value} in ConfStore"
                )
                PillarSet().run(
                    f'cluster/storage_set/durability/{durability_type}/{key}',
                    value,
                    targets=node_id,
                    local=True
                )
                Conf.set(
                    index,
                    f'cluster>storage_set>durability>{durability_type}>{key}',
                    value
                )

        Conf.save(index)
        self.logger.info("Storageset Durability configured")
