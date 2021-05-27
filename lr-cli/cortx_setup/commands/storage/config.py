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
from .commons import Commons

#TODO: Add this path in the global config
prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)


"""Cortx Setup API for configuring the storage enclosure """


class StorageEnclosureConfig(command):
    '''
    $ cortx_setup storage --name <Enclosure name>

    $ cortx_setup storage --type <Enclosure type>
    '''
    _args = {
        'name': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Set name of the enclosure e.g enc1-r10'
        },
        'type': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Enclosure type e.g {RBOD | JBOD | EBOD | virtual}'
        },
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
            'help': 'Type of controller e.g {gallium | indium | virtual}'
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

    def run(self, name=None, type=None,
            user=None, password=None, type=None, mode=None,
            ip=None, port=None):

        node_id = local_minion_id()
        enc_num = "enclosure-" + ((node_id).split('-'))[1]
        enc_id = commons.get_enc_id(target=node_id)

        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )
        if name is not None:
            self.logger.info(
                f"Updating storage enclosure name to {name} in confstore"
            )
            PillarSet().run(
                f'storage/{node_id}/{enc_num}/name',
                f'{name}',
                targets=node_id,
                local=True
            )
            Conf.set(
                'node_info_index',
                f'storage_enclosure>{enc_id}>name',
                name
            )
        if type is not None:
            self.logger.info(
                f"Updating storage enclosure type to {type} in confstore"
            )
            PillarSet().run(
                f'storage/{node_id}/{enc_num}/type',
                f'{type}',
                targets=node_id,
                local=True
            )
            Conf.set(
                'node_info_index',
                f'storage_enclosure>{enc_id}>type',
                type
            )
        if user is not None:
            self.logger.info(
                f"Updating controller user to {user} in confstore"
            )
            PillarSet().run(
                f'storage/{node_id}/{enc_num}/controller/user',
                f'{user}',
                targets=node_id,
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
                targets=node_id,
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
                targets=node_id,
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
                    targets=node_id,
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
                    targets=node_id,
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
