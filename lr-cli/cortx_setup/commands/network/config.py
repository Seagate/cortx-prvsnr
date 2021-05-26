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

from pathlib import Path
from ..command import Command
from ..config import PRVSNR_CLUSTER_CONFSTORE
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id, function_run


"""Cortx Setup API for configuring network"""


class NetworkConfig(Command):
    _args = {
        'transport_type': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Transport type for network e.g {lnet|libfabric}'
        },
        'interface_type': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Interface type for network e.g {tcp|o2ib}'
        },
        'network_type': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['data', 'mgmt'],
            'help': 'Network type for provided interfaces'
        },
        'interfaces': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of interfaces for provided network_type '
                    'e.g eth1 eth2'
        },
        'private': {
            'default': False,
            'optional': True,
            'action': 'store_true',
            'help': 'Use provided interfaces for private network'
        }
    }

    def run(self, transport_type=None, interface_type=None, network_type=None,
            interfaces=None, private=False):
        node_id = local_minion_id()
        machine_id = utils.get_machine_id(target=node_id)
        Conf.load(
            'node_config_index',
            f'json://{PRVSNR_CLUSTER_CONFSTORE}'
        )

        if transport_type is not None:
            self.logger.info(
                f"Updating transport type to {transport_type} in confstore"
            )
            PillarSet().run(
                f'cluster/{node_id}/network/data/transport_type',
                f'{transport_type}',
                targets=node_id,
                local=True
            )
            self.Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>network>data>transport_type',
                transport_type
            )

        elif interface_type is not None:
            self.logger.info(
                f"Updating interface type to {interface_type} in confstore"
                )
            PillarSet().run(
                f'cluster/{node_id}/network/data/interface_type',
                f'{interface_type}',
                targets=node_id,
                local=True
            )
            self.Conf.set(
                'node_config_index',
                f'server_node>{machine_id}>network>data>interface_type',
                interface_type
            )

        elif interfaces is not None:
            if network_type == 'data':
                iface_key = (
                    'private_interfaces' if private else 'public_interfaces'
                )
                self.logger.info(
                    f"Updating {iface_key} for data network "
                    "in confstore"
                )
                PillarSet().run(
                    f'cluster/{node_id}/network/data/{iface_key}',
                    interfaces,
                    targets=node_id,
                    local=True
                )
                self.Conf.set(
                    'node_config_index',
                    f'server_node>{machine_id}>network>data>{iface_key}',
                    interfaces
                )
            elif network_type == 'mgmt':
                self.logger.info(
                    "Updating interfaces for management network "
                    "in confstore"
                )
                PillarSet().run(
                    f'cluster/{node_id}/network/mgmt/interfaces',
                    interfaces,
                    targets=node_id,
                    local=True
                )
                self.Conf.set(
                    'node_config_index',
                    f'server_node>{machine_id}>network>management>interfaces',
                    interfaces
                )
            else:
                self.logger.error(
                    "Network type should specified for provided interfaces"
                )
        else:
            self.logger.error("No parameters provided to configure network")
        self.Conf.save('node_config_index')
        self.logger.info("Done")
