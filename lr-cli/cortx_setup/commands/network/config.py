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
from cortx_setup.config import CONFSTORE_CLUSTER_FILE, BMC_COMPONENT
from cortx_setup.commands.common_utils import get_machine_id, encrypt_secret
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx_setup.validate import ipv4


class NetworkConfig(Command):
    _args = {
        'mode': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['tcp', 'o2ib'],
            'help': 'Network  interface type'
        },
        'transport': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['lnet', 'libfabric'],
            'help': 'Network transport type'
        },
        'bmc': {
            'type': ipv4,
            'default': None,
            'optional': True,
            'help': 'BMC IP for the system'
        },
        'user': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'BMC user for system'
        },
        'password': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'BMC password for system'
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

    def run(self, mode=None, transport=None, network_type=None, interfaces=None,
            bmc=None, user=None, password=None):

        """Network config execution method.

        Execution:
        `cortx_setup network config --transport lnet`
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

        if bmc is not None:
            self.logger.debug(
                f"Set BMC IP to {bmc}"
            )
            PillarSet().run(
                f'cluster/{node_id}/bmc/ip',
                f'{bmc}',
                local=True
            )
            Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>bmc>ip',
                bmc
            )
        if user is not None:
            self.logger.debug(
                f"Set BMC user to {user}"
            )
            PillarSet().run(
                f'cluster/{node_id}/bmc/user',
                f'{user}',
                local=True
            )
            Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>bmc>user',
                user
            )
        if password is not None:
            self.logger.debug(
                f"Set BMC password to {password}"
            )
            PillarSet().run(
                f'cluster/{node_id}/bmc/secret',
                f'{password}',
                local=True
            )
            secret = encrypt_secret(password, BMC_COMPONENT, machine_id)
            Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>bmc>secret',
                secret
            )

        if mode is not None:
            mode_type = 'interface_type'
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
        if transport is not None:
            mode_type = 'transport_type'
            self.logger.debug(
                f"Set {mode_type} to {mode}"
            )
            PillarSet().run(
                f'cluster/{node_id}/network/data/{mode_type}',
                f'{transport}',
                local=True
            )
            Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>network>data>{mode_type}',
                transport
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
