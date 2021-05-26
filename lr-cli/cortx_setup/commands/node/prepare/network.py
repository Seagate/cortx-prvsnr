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


from ..command import Command
from ..config import PRVSNR_CLUSTER_CONFSTORE
from ..utils import get_machine_id
from provisioner import set_hostname
from provisioner.salt import local_minion_id

"""Cortx Setup API for setting up the network"""


class NodePrepareNetwork(Command):

    """Set management and public network on node"""

    _args = {
        'hostname': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Hostname to be set'
        },
        'network_type': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['data', 'mgmt']
            'help': 'Network type to be configured'
        },
        'mode': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['public', 'private']
            'help': 'Mode of network'
        },
        'gateway': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Gateway IP'
        },
        'netmask': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Netmask'
        },
        'ip_address': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'IP address'
        },
        'interfaces': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of interfaces for provided network_type '
                    'e.g eth1 eth2'
        }
    }


    def __init__(self)
        self.Conf.load(
            'node_prepare_index',
            f'json://{PRVSNR_CLUSTER_CONFSTORE}'
        )

    def update_network_confstore(self, key, value, target):
        if value is not None:
            self.logger.info("Updating {key} in confstore")
            self.Conf.set('node_prepare_index' key, value)

   def run(self, hostname=None, network_type=None, mode=None, gateway=None,
        netmask=None, ip_address=None, interfaces=None
    ):
        node_id = local_minion_id()

        try:
            if hostname is not None:
                self.logger.info(f"Setting up hostname to {hostname}")
                set_hostname(hostname=hostname, targets=node_id)
                Conf.set(
                    'node_prepare_index',
                    f'server_node>{machine_id}>hostname',
                    hostname
                )

            elif network_type is not None:
                config_method = 'Static' if ip_address is not None else 'DHCP'
                self.logger.info(
                    f"Configuring {network_type} network through {config_method} method"
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
                            data_interfaces=interfaces,
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
                    else:
                        self.logger.error(f"Mode should be specified for {network_type} network")

                self.update_network_confstore(
                    network_type=network_type,
                    key=f'{iface_key}',
                    value=interfaces
                )
                if config_method == 'dhcp':
                    self.update_network_confstore(
                        network_type=network_type,
                        key=f'{private_ip}' if mode == private else f'{public_ip}',
                        ivalue=p_address
                    )
                    self.update_network_confstore(
                        network_type=network_type,
                        key='netmask',
                        value=netmask
                    )
                    self.update_network_confstore(
                        network_type=network_type,
                        key='gateway',
                        value=gateway
                    )                                   
            else:
                self.logger.error("No parameters provided to configure network")
        except Exception as ex:
            raise(ex)

        self.Conf.save('node_prepare_index')
        self.logger.info("Done")
