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
from cortx_setup.commands.command import Command
from cortx_setup.validate import ipv4, host
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet


prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)


"""Cortx Setup API for configuring network"""


class ClusterNetworkConfig(Command):
    _args = {
        'virtual_host': {
            'type': ipv4,
            'default': None,
            'optional': True,
            'help': 'Cluster vip'
        },
        'search_domains': {
            'type': host,
            'nargs': '+',
            'optional': True,
            'help': 'List of search domains for provided network '
        },
        'dns_servers': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of DNS for provided network '
        }
    }

    def run(self, **kwargs):
        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )
        for key, value in kwargs.items():
            if value:
                self.logger.debug(
                    f"Updating {key} to {value} in confstore"
                )
                PillarSet().run(
                    f'cluster/{key}',
                    value,
                    local=True
                )
                Conf.set(
                    'node_info_index',
                    f'cluster>{key}',
                    value
                )

        Conf.save('node_info_index')
        self.logger.debug("Done")
