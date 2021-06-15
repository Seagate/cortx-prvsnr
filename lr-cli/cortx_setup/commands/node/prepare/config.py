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

from cortx.utils.conf_store import Conf
from cortx_setup.validate import ipv4
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx_setup.commands.common_utils import (
    get_machine_id
)

from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE


node = local_minion_id()


class NodePrepareServerConfig(Command):
    _args = {
        'site_id': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Site ID'
        },
        'rack_id': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Rack ID'
        },
        'node_id': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Node ID'
        },
        'mgmt_vip': {
            'type': ipv4,
            'default': None,
            'optional': True,
            'help': 'Management VIP'
        },
        'primary': {
            'optional': True,
            'action': 'store_true',
            'help': 'Set node as a primary node'
        }
    }

    def run(self, **kwargs):
        """Cortx Setup API for configuring Node Prepare Server"""

        machine_id = get_machine_id(node)

        # Prepare a mapping for pillar-key to confstore-key
        confstore_pillar_dict = {
            'site_id': (
                f'server_node>{machine_id}>site_id',
                f'cluster/{node}/site_id'),
            'rack_id': (
                f'server_node>{machine_id}>rack_id',
                f'cluster/{node}/rack_id'),
            'node_id': (
                f'server_node>{machine_id}>node_id',
                f'cluster/{node}/node_id')
        }

        # Load confstore
        Conf.load(
            'node_info_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )

        for key, value in kwargs.items():
            if value:
                self.logger.debug(
                    f"Updating {key} to {value} in confstore"
                )
                if key in confstore_pillar_dict.keys():
                    PillarSet().run(
                        confstore_pillar_dict[key][1],
                        value,
                        local=True
                    )
                    Conf.set(
                        'node_info_index',
                        confstore_pillar_dict[key][0],
                        value
                    )
        # set management vip
        # we are not updating mgmt_vip to confstore
        # as there is no cluster_id so only setting it in pillars
        # In further steps when we export confstore it would add it to
        # confstore.
        PillarSet().run(
            f'cluster/mgmt_vip',
            kwargs['mgmt_vip'],
            local=True)

        node_roles = ['primary'] if kwargs['primary'] else ['secondary']
        # set node roles
        PillarSet().run(
            f"cluster/{node}/roles",
            node_roles,
            local=True
        )

        Conf.save('node_info_index')
        self.logger.debug("Done")
