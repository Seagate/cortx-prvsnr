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
from pathlib import Path
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id


prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)


class ClusterCreate(Command):
    _args = {
        'name': {
            'type': str,
            'default': 'cortx_cluster',
            'optional': True},
        'site_count': {
            'type': int,
            'default': 1,
            'optional': True},
        'storageset_count': {
            'type': int,
            'default': 1,
            'optional': True}
    }

    def run(self, **kwargs):
        node_id = local_minion_id()
        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )
        for key, value in kwargs.items():
            if value:
                self.logger.info(
                    f"Updating {key} to {value} in confstore"
                )
                PillarSet().run(
                    f'cluster/{key}',
                    value,
                    targets=node_id,
                    local=True
                )
                Conf.set(
                    'node_info_index',
                    f'cluster>{key}',
                    value
                )

        Conf.save('node_info_index')
        self.logger.info("Done")
