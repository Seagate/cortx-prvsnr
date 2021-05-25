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
# from ..config import CONFSTORE_CLUSTER_FILE

from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx.utils.conf_store import Conf

prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)


class CreateStorageSet(Command):
    _args = {
        'name': {
            'type': str,
            'default': 'storage-set',
            'optional': True
        },
        'count': {
            'type': int,
            'default': 1,
            'optional': True
        }
    }

    def run(self, **kwargs):
        node_id = local_minion_id()
        index = 'storageset_index'

        Conf.load(
            index,
            f'json://{prvsnr_cluster_path}'
        )
        for key, value in kwargs.items():
            if value:
                self.logger.info(
                    f"Updating {key} as {value} in ConfStore"
                )
                PillarSet().run(
                    f'cluster/storage_set/{key}',
                    value,
                    targets=node_id,
                    local=True
                )
                Conf.set(
                    index,
                    f'cluster>storage_set>{key}',
                    value
                )

        Conf.save(index)
        self.logger.info("Storageset created")
