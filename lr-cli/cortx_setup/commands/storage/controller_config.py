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
from cortx.utils.conf_store import Conf
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id, function_run

prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)


"""Cortx Setup API for configuring the storage controller"""

class StorageControllerConfig(Command):
    '''
    $ cortx_setup storage controller --user <user> --password <password>

    $ cortx_setup storage controller --type (Gallium | Indium | virtual)

    $ cortx_setup storage controller --mode (primary | secondary) --ip <ip-address> --port <port-number>
    '''
    _args = {
        'user': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'username for controller e.g {manage}'
        },
        'password': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'password for controller user'
        },
        'type': {
            'type': str,
            'optional': True,
            'help': 'Type of controller e.g {Gallium | Indium | virtual}'
        },
        'mode': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Controller mode e.g. {primary | secondary}'
        },
        'ip': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'IP address of the controller'
        },
        'port': {
            'type': str,
            'default': False,
            'optional': True,
            'help': 'Port of the controller to connect to'
        }
    }

    def get_enc_id(self, targets):
        try:
            result = function_run('grains.get', fun_args=['machine_id'],
                                targets=targets)
            _enc_id = result[f'{targets}']
        except Exception as exc:
            raise exc
        return _enc_id

    def run(self, user=None, password=None, type=None, mode=None,
                ip=None, port=None
    ):
        node_id = local_minion_id()
        enc_num = "enclosure-1" #TODO: Generate this
        enc_id = self.get_enc_id(target=node_id) #TODP: define this

        #machine_id = self.get_machine_id(targets=node_id)
        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )
        if user is not None:
            self.logger.info(
                f"Updating controller user to {user} in confstore"
            )
            PillarSet().run(
                f'storage/{node_id}/{enc_num}/controller/user',
                f'{user}',
                targets=node_id, #TODO: correct this
                local=True
            )
            Conf.set(
                'node_info_index',
                f'storage_enclosure>{enc_id}>controller>user',
                user
            )
        if password is not None:
            self.logger.info(
                f"Updating controller secret in confstore"
            )
            PillarSet().run(
                f'storage/{node_id}/{enc_num}/controller/secret',
                f'{secret}',
                targets=node_id, #TODO: correct this
                local=True
            )
            Conf.set(
                'node_info_index', #Is this correct?
                f'storage_enclosure>{enc_id}>controller>secret',
                secret
            )
        if type is not None:
            self.logger.info(
                f"Updating controller type in confstore"
            )
            PillarSet().run(
                f'storage/{node_id}/{enc_num}/controller/type',
                f'{type}',
                targets=node_id, #TODO: correct this
                local=True
            )
            Conf.set(
                'node_info_index', #Is this correct?
                f'storage_enclosure>{enc_id}>controller>type',
                type
            )
        if mode is not None:
            set_ip = False
            set_port = False

            self.logger.info(
                f"Updating {mode} controller IP/port in confstore"
            )
            if ip is not None:
                self.logger.info(
                    f"Updating {mode} controller IP in confstore"
                )
                PillarSet().run(
                    f'storage/{node_id}/{enc_num}/controller/{mode}/ip',
                    f'{ip}',
                    targets=node_id, #TODO: correct this
                    local=True
                )
                Conf.set(
                    'node_info_index', #Is this correct?
                    f'storage_enclosure>{enc_id}>controller>{mode}/ip',
                    ip
                )
                set_ip = True
            if port is not None:
                self.logger.info(
                    f"Updating {mode} controller port in confstore"
                )
                PillarSet().run(
                    f'storage/{node_id}/{enc_num}/controller/{mode}/port',
                    f'{port}',
                    targets=node_id, #TODO: correct this
                    local=True
                )
                Conf.set(
                    'node_info_index', #Is this correct?
                    f'storage_enclosure>{enc_id}>controller>{mode}/port',
                    port
                )
                set_port = True
            if not True in set_ip and set_port:
                self.logger.info(
                    f"Please provide correct options for {mode}"
                ) 

