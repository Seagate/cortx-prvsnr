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
from cortx.utils.conf_store import Conf
from cortx_setup.commands.common_utils import get_machine_id
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from provisioner.salt import local_minion_id
from provisioner.commands import PillarSet


class ServerConfig(Command):

    _args = {
        'name': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Set name of the server'
        },
        'type': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['VM', 'HW'],
            'help': 'Server type e.g {VM|HW}'
        }
    }


    def run(self, **kwargs):
        """
        Server configuration command execution method

        Command:
        `cortx_setup server config --name <name> --type {VM|HW}}`
        """

        node_id = local_minion_id()
        machine_id = get_machine_id(node_id)

        conf_pillar_map = {
            'name': (
                f'cluster/{node_id}/name',
                f'server_node>{machine_id}>name'
            ),
            'type': (
                f'cluster/{node_id}/type',
                f'server_node>{machine_id}>type'
            )
        }

        Conf.load(
            'node_info_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )

        for key, value in kwargs.items():
            if value:
                if key in conf_pillar_map.keys():
                    self.logger.debug(f"Updating pillar with key:{conf_pillar_map[key][0]} and value:{value}")
                    PillarSet().run(
                        conf_pillar_map[key][0],
                        value,
                        local=True
                    )
                    self.logger.debug(f"Updating confstore with key:{conf_pillar_map[key][1]} and value:{value}")
                    Conf.set(
                        'node_info_index',
                        conf_pillar_map[key][1],
                        value
                    )

        Conf.save('node_info_index')
        self.logger.debug("Done")
