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

# Cortx Setup API for Preparing network in field

from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx_setup.validate import host, ipv4
from cortx_setup.commands.common_utils import get_machine_id
from provisioner import (
    set_hostname,
    set_mgmt_network,
    set_public_data_network,
    set_private_data_network
)
from provisioner.salt import local_minion_id, function_run, StatesApplier
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet


class NodePrepareNetwork(Command):
    _args = {
        'hostname': {
            'type': host,
            'optional': True,
            'default': None,
            'help': 'Hostname to be set'
        },
        'type': {
            'type': str,
            'optional': True,
            'default': None,
            'dest': 'network_type',
            'choices': ['data', 'private', 'management'],
            'help': 'Type of network to prepare'
        },
        'gateway': {
            'type': ipv4,
            'optional': True,
            'default': "",
            'help': 'Gateway IP'
        },
        'netmask': {
            'type': ipv4,
            'optional': True,
            'default': "",
            'help': 'Netmask'
        },
        'ip_address': {
            'type': ipv4,
            'optional': True,
            'default': "",
            'help': 'IP address'
        },
        'dns_servers': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of DNS servers for the provided network, given space-separated'
        },
        'search_domains': {
            'type': host,
            'nargs': '+',
            'optional': True,
            'help': 'List of Search domains for the provided network, given space-separated'
        },
    }

    def update_network_confstore(self, network_type, key, value, target):

        """
        Set network parameters in confstore
        Parameters
        ----------
        network_type: str
            Type of network
        key: str
            Confstore key to update
        value: str
            Value to set
        target: str
            Node id
        """

        machine_id = get_machine_id(target)
        if value:
            self.logger.debug(
                f"Set {network_type} network {key} to {value}"
            )
            if network_type == 'private':
                network_type = 'data'
            Conf.set(
                'node_prepare_index',
                f'server_node>{machine_id}>network>{network_type}>{key}',
                value
            )

    def run(self, hostname=None, network_type=None, gateway=None, netmask=None,
        ip_address=None, dns_servers=None, search_domains=None
    ):

        """Network prepare execution method.

        Execution:
        `cortx_setup node prepare network --hostname <hostname>`
        `cortx_setup node prepare network --type <type> --ip_address <ip_address>
                --netmask <netmask> --gateway <gateway> --dns_servers <dns server>
		--search_domains <search domains>`
        """

        node_id = local_minion_id()
        machine_id = get_machine_id(node_id)
        Conf.load(
            'node_prepare_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )

        if hostname is not None:
            self.logger.debug(f"Setting up system hostname to {hostname}")
            try:
                set_hostname(hostname=hostname, local=True)
                Conf.set(
                    'node_prepare_index',
                    f'server_node>{machine_id}>hostname',
                    hostname
                )
            except Exception as ex:
                raise ex

        if network_type is not None:

            server_type = function_run('grains.get', fun_args=['virtual'],
                                targets=node_id)[f'{node_id}']
            if not server_type:
                raise Exception("server_type missing in grains")
            mtu = '1500' if server_type == 'virtual' or network_type == 'management' else '9000'

            config_method = 'Static' if ip_address else 'DHCP'
            self.logger.debug(
                f"Configuring {network_type} network using {config_method} method"
            )

            try:
                if network_type == 'management':
                    set_mgmt_network(
                        mgmt_public_ip=ip_address,
                        mgmt_netmask=netmask,
                        mgmt_gateway=gateway,
                        mgmt_mtu=mtu,
                        local=True
                    )
                elif network_type == 'data':
                    set_public_data_network(
                        data_public_ip=ip_address,
                        data_netmask=netmask,
                        data_gateway=gateway,
                        data_mtu=mtu,
                        local=True
                    )
                elif network_type == 'private':
                    set_private_data_network(
                        data_private_ip=ip_address,
                        data_mtu=mtu,
                        local=True
                    )
            except Exception as ex:
                raise ex

            if config_method == 'Static':
                self.update_network_confstore(
                    network_type=network_type,
                    key='private_ip' if network_type == 'private' else 'public_ip',
                    value=ip_address, target=node_id
                )
                self.update_network_confstore(
                    network_type=network_type, key='netmask', value=netmask, target=node_id
                )
                self.update_network_confstore(
                    network_type=network_type, key='gateway', value=gateway, target=node_id
                )
        for key, val in {'dns_servers': dns_servers, 'search_domains': search_domains}.items():
            if val:
                self.logger.debug(f"Setting up system {key} to {val}")
                conf_key = f'cluster>networks>{key}'
                Conf.set(
                    'node_prepare_index', conf_key, val)
                PillarSet().run(f'cluster/{key}', val, local=True)
        function_run('saltutil.refresh_pillar', targets=node_id)
        if dns_servers and search_domains:
            StatesApplier.apply(
                ["components.system.network.resolv_conf"],
                local_minion_id()
            )

        Conf.save('node_prepare_index')
        # call state applyer if dns n search doma:wq

        self.logger.debug("Done")
