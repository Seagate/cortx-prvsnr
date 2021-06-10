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

# Cortx Setup API for configuring network

from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx_setup.commands.common_utils import get_machine_id
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id


class NetworkConfig(Command):
    _args = {
        'mode': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['lnet', 'libfabric', 'tcp', 'o2ib'],
            'help': 'Network transport or interface type'
        },
        'type': {
            'type': str,
            'default': None,
            'optional': True,
            'dest': 'network_type',
            'choices': ['data', 'private', 'management'],
            'help': 'Type of network to configure'
        },
        'interfaces': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of interfaces e.g eth1 eth2'
        }
    }

    def run(self, mode=None, network_type=None, interfaces=None):

        """Network config execution method.

        Execution:
        `cortx_setup network config --mode lent`
        `cortx_setup network config --mode tcp`
        `cortx_setup network config --type mgmt --interfaces eth0`
        `cortx_setup network config --type data --interfaces eth1 eth2`
        `cortx_setup network config --type private --interfaces eth3 eth4`

        """

        node_id = local_minion_id()
        machine_id = get_machine_id(node_id)
        Conf.load(
            'node_config_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )

        if mode is not None:
            mode_type = 'transport_type' if mode in ['lnet', 'libfabric'] else 'interface_type'
            self.logger.debug(
                f"Set {mode_type} to {mode}"
            )
            PillarSet().run(
                f'cluster/{node_id}/network/data/{mode_type}',
                f'{mode}',
                local=True
            )
            Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>network>data>{mode_type}',
                mode
            )
        if interfaces is not None:
            if network_type == 'data' or network_type == 'private':
                iface_key = (
                    'private_interfaces' if network_type == 'private' else 'public_interfaces'
                )
                self.logger.debug(
                    f"Set {iface_key} to {interfaces} for {network_type} network"
                )
                PillarSet().run(
                    f'cluster/{node_id}/network/data/{iface_key}',
                    interfaces,
                    local=True
                )
                Conf.set(
                    'node_config_index',
                    f'server_node>{machine_id}>network>data>{iface_key}',
                    interfaces
                )
            elif network_type == 'management':
                self.logger.debug(
                    f"Set interfaces to {interfaces} for {network_type} network"
                )
                PillarSet().run(
                    f'cluster/{node_id}/network/mgmt/interfaces',
                    interfaces,
                    local=True
                )
                Conf.set(
                    'node_config_index',
                    f'server_node>{machine_id}>network>management>interfaces',
                    interfaces
                )
            else:
                raise Exception(
                    "Network type should specified for provided interfaces"
                )
        Conf.save('node_config_index')
        self.logger.debug("Done")
