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
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from ...common_utils import (
    get_machine_id,
    get_cluster_id
)

from ...command import Command
from ....config import CONFSTORE_CLUSTER_FILE


node = local_minion_id()
machine_id = get_machine_id(node)
cluster_id = get_cluster_id()

confstore_pillar_dict = {
    'site_id': (
        f'server_node>{machine_id}>site_id',
        f'cluster/{node}/site_id'),
    'rack_id': (
        f'server_node>{machine_id}>rack_id',
        f'cluster/{node}/rack_id'),
    'node_id': (
        f'server_node>{machine_id}>node_id',
        f'cluster/{node}/node_id'),
    'mgmt_vip': (
        f'cluster>{cluster_id}>network>management>virtual_host',
        'cluster/mgmt_vip')}


"""Cortx Setup API for configuring Node Prepare Server"""


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
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Management VIP'
        }

    }

    def run(self, **kwargs):
        Conf.load(
            'node_info_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )

        for key, value in kwargs.items():
            if value:
                self.logger.debug(
                    f"Updating {key} to {value} in confstore"
                )
                PillarSet().run(
                    confstore_pillar_dict[key][1],
                    value,
                    targets=node,
                    local=True
                )
                Conf.set(
                    'node_info_index',
                    confstore_pillar_dict[key][0],
                    value
                )

        Conf.save('node_info_index')
        self.logger.debug("Done")
