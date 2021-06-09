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
from provisioner.api import grains_get, pillar_get
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from .commons import EnclosureInfo

#TODO: Add this path in the global config
prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)

enc_file_path = Path(
    '/etc/enclosure-id'
)

"""Cortx Setup API for configuring the storage enclosure """


class StorageEnclosureConfig(Command):
    '''
    $ cortx_setup storage config --user <user> --password <password> --ip <ip-address> --port <port-number>
    $ cortx_setup storage config --name <enclosure-name>
    $ cortx_setup storage config --type {RBOD|JBOD|EBOD|virtual}
    $ cortx_setup storage config --controller_type {gallium|indium|virtual}
    $ cortx_setup storage config --mode {primary|secondary} --ip <ip-address> --port <port-number>
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
        'controller_type': {
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
            'default': None,
            'optional': True,
            'help': 'Port of the controller to connect to'
        }
    }

    def __init__(self):
        super().__init__()
        self.node_id = local_minion_id()
        self.enc_num = "enclosure-" + ((self.node_id).split('-'))[1]
        self.flag = False

        if enc_file_path.exists():
            if Path(enc_file_path).stat().st_size != 0:
                self.flag = True
                with open(enc_file_path, "r") as file:
                    self.enclosure_id = file.read().replace('\n', '')
        else:
            self.enclosure_id = None

    def store_enclosure_id(self):

        # store to /etc/enclosure-id file
        self.logger.debug(f"Writing storage enclosure_id to the file {enc_file_path}")
        file = open(enc_file_path, "w")
        file.write(self.enclosure_id + "\n")
        file.close()

        # store to pillar
        self.logger.debug(f"Updating storage enclosure_id to {self.enclosure_id} in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/enclosure_id',
            f'{self.enclosure_id}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating storage enclosure_id to {self.enclosure_id} in Cortx ConfStor")
        machine_id = grains_get("machine_id")[self.node_id]["machine_id"]
        Conf.set(
            'node_info_index',
            f'server_node>{machine_id}>storage>enclosure_id',
            self.enclosure_id
        )

    def store_user_and_pass(self, user, password):

        # store to pillar
        self.logger.debug(f"Updating storage enclosure user to {user} in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/controller/user',
            f'{user}',
            targets=self.node_id,
            local=True
        )

        self.logger.debug(f"Updating storage enclosure password to {password} in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/controller/secret',
            f'{password}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating storage enclosure user to {user} in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>controller>user',
            user
        )

        self.logger.debug(f"Updating storage enclosure secret to {password} in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>controller>secret',
            password
        )

    def store_ip(self, mode, ip):

        #store to pillar
        self.logger.debug(f"Updating {mode} controller IP [{ip}] in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/controller/{mode}/ip',
            f'{ip}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating {mode} controller IP [{ip}] in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>controller>{mode}>ip',
            ip
        )

    def store_port(self, mode, port):

        # store to pillar
        self.logger.debug(f"Updating {mode} controller port [{port}] in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/controller/{mode}/port',
            f'{port}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating {mode} controller port [{port}] in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>controller>{mode}>port',
            port
        )

    def store_name(self, name):
        # store to pillar
        self.logger.debug(f"Updating storage enclosure name to {name} in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/name',
            f'{name}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating storage enclosure name to {name} in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>name',
            name
        )

    def store_storage_type(self, storage_type):

        # store to pillar
        self.logger.debug(f"Updating storage type to {storage_type} in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/type',
            f'{storage_type}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating storage type to {storage_type} in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>type',
            storage_type
        )

    def store_controller_type(self, controller_type):

        # store to pillar
        self.logger.debug(f"Updating controller type to {controller_type} in pillar")
        PillarSet().run(
            f'storage/{self.enc_num}/controller/type',
            f'{controller_type}',
            targets=self.node_id,
            local=True
        )

        # store to confstore
        self.logger.debug(f"Updating controller type to {controller_type} in Cortx ConfStor")
        Conf.set(
            'node_info_index',
            f'storage_enclosure>{self.enclosure_id}>controller>type',
            controller_type
        )



    def run(self, **kwargs):

        user = kwargs.get('user')
        password = kwargs.get('password')
        ip = kwargs.get('ip')
        port = kwargs.get('port')

        name = kwargs.get('name')
        storage_type = kwargs.get('type')
        controller_type = kwargs.get('controller_type')
        mode = kwargs.get('mode')

        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )

        if user != None and password != None and ip != None and port != None:
            # fetch enclosure serial/id
            self.enclosure_id = EnclosureInfo(ip, user, password, port).get_enclosure_serial()

            # store enclosure_id
            self.store_enclosure_id()

            # store user and password
            self.store_user_and_pass(user, password)

            # store ip and port as primary
            self.store_ip("primary", ip)
            self.store_port("primary", port)
        else:
            if name is not None:
                if self.flag:
                    self.store_name(name)
                else:
                    self.logger.error("Please set 'user, password, primary ip and port' first")
                    raise RuntimeError("Cannot set name before setting user, password, ip and port")


            if storage_type is not None:
                if self.flag:
                    self.store_storage_type(storage_type)
                else:
                    self.logger.error("Please set 'user, password, primary ip and port' first")
                    raise RuntimeError("Cannot set storage_type before setting user, password, ip and port")


            if controller_type is not None:
                if self.flag:
                    self.store_controller_type(controller_type)
                else:
                    self.logger.error("Please set 'user, password, primary ip and port' first")
                    raise RuntimeError("Cannot set storage_type before setting user, password, ip and port")

            if mode is not None:
                if ip is None and port is None:
                    self.logger.exception(
                        f"Sub options for mode {mode} are missing"
                    )
                    raise RuntimeError('Please provide ip and/or port')

                if self.flag:
                    if ip:
                        self.store_ip(mode, ip)

                    if port:
                        self.store_port(mode, port)
                else:
                    self.logger.error("Please provide user and password as well")
                    raise RuntimeError("Incomplete arguments provided")

            if user is not None and password is not None:
                if self.flag:
                    host = pillar_get(f"storage/{self.enc_num}/controller/primary/ip")[self.node_id][f'storage/{self.enc_num}/controller/primary/ip']
                    port = pillar_get(f"storage/{self.enc_num}/controller/primary/port")[self.node_id][f'storage/{self.enc_num}/controller/primary/port']

                    valid_connection_check = EnclosureInfo(host, user, password, port).connection_status()

                    if valid_connection_check:
                        self.set_user_and_pass(user, password)
                    else:
                        self.logger.error(f"Cannot establish connection with enclosure using user={user} and password={password} as credentials")
                        raise ValueError("Invalid credentials provided")
                else:
                    self.logger.error("Please provide ip and port as well")
                    raise RuntimeError("Incomplete arguments provided")

        Conf.save('node_info_index')
        self.logger.debug("Done")
