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

from cortx_setup.commands.command import Command
from cortx_setup.config import PRVSNR_CLUSTER_CONFSTORE
from cortx_setup import utils
from provisioner import (
    set_hostname,
    set_mgmt_network,
    set_public_data_network,
    set_private_data_network
)
from provisioner.salt import local_minion_id
from cortx.utils.conf_store import Conf


class NodePrepareNetwork(Command):
    _args = {
        'hostname': {
            'type': str,
            'optional': True,
            'default': None,
            'help': 'Hostname to be set'
        },
        'type': {
            'type': str,
            'optional': True,
            'default': None,
            'dest': 'network_type'
            'choices': ['data', 'mgmt'],
            'help': 'Network type to be configured'
        },
        'mode': {
            'type': str,
            'optional': True,
            'default': 'public',
            'choices': ['public', 'private'],
            'help': 'Mode of network'
        },
        'gateway': {
            'type': str,
            'optional': True,
            'default': "",
            'help': 'Gateway IP'
        },
        'netmask': {
            'type': str,
            'optional': True,
            'default': "",
            'help': 'Netmask'
        },
        'ip_address': {
            'type': str,
            'optional': True,
            'default': "",
            'help': 'IP address'
        },
        'interfaces': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'default': "",
            'help': 'List of interfaces for provided type '
                    'e.g eth1 eth2'
        }
    }

    def update_network_confstore(self, network_type, key, value, target):
        machine_id = utils.get_machine_id(target=target)
        if value:
            self.logger.debug(
                f"Updating {key} to {value} for {network_type} network in confstore"
            )
            Conf.set(
                'node_prepare_index',
                f'server_node>{machine_id}>network>{network_type}>{key}',
                value
            )

    def run(self, hostname=None, network_type=None, mode=None, gateway=None,
        netmask=None, ip_address=None, interfaces=None
    ):
        node_id = local_minion_id()
        machine_id = utils.get_machine_id(target=node_id)
        Conf.load(
            'node_prepare_index',
            f'json://{PRVSNR_CLUSTER_CONFSTORE}'
        )

        if hostname is not None:
            self.logger.debug(f"Setting up hostname to {hostname}")
            set_hostname(hostname=hostname, targets=node_id, local=True)
            Conf.set(
                'node_prepare_index',
                f'server_node>{machine_id}>hostname',
                hostname
            )

        if network_type is not None:
            config_method = 'Static' if ip_address else 'DHCP'
            self.logger.debug(
                f"Configuring {network_type} network "
                f"through {config_method} method"
            )

            if network_type == 'mgmt':
                network_type = 'management'
                iface_key = 'interfaces'
                set_mgmt_network(
                    mgmt_public_ip=ip_address,
                    mgmt_netmask=netmask,
                    mgmt_gateway=gateway,
                    mgmt_interfaces=interfaces,
                    local=True,
                    targets=node_id
                )
            elif network_type == 'data':
                if mode == 'public':
                    iface_key = 'public_interfaces'
                    set_public_data_network(
                        data_public_ip=ip_address,
                        data_netmask=netmask,
                        data_gateway=gateway,
                        data_public_interfaces=interfaces,
                        local=True,
                        targets=node_id
                    )
                elif mode == 'private':
                    iface_key = 'private_interfaces'
                    set_private_data_network(
                        data_private_ip=ip_address,
                        data_private_interfaces=interfaces,
                        local=True,
                        targets=node_id
                    )
            self.update_network_confstore(
                type=network_type,
                key=iface_key,
                value=interfaces,
                target=node_id
            )
            if config_method == 'Static':
                self.update_network_confstore(
                    type=network_type,
                    key='private_ip' if mode == 'private' else 'public_ip',
                    value=ip_address,
                    target=node_id
                )
                self.update_network_confstore(
                    type=network_type,
                    key='netmask',
                    value=netmask,
                    target=node_id
                )
                self.update_network_confstore(
                    type=network_type,
                    key='gateway',
                    value=gateway,
                    target=node_id
                )
        Conf.save('node_prepare_index')
        self.logger.debug("Done")
