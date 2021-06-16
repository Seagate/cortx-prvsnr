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
from cortx_setup.commands.common_utils import get_machine_id
from provisioner.api import grains_get, pillar_get
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from .enclosure_info import EnclosureInfo

#TODO: Add this path in the global config
prvsnr_cluster_path = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)

enc_file_path = Path(
    '/etc/enclosure-id'
)

node_id = local_minion_id()
enc_num = "enclosure-" + ((node_id).split('-'))[1]

conf_pillar_map = {}

"""Cortx Setup API for configuring the storage enclosure """


class StorageEnclosureConfig(Command):
    """
        Cortx Setup API for configuring Storage Enclosure
    """

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
            'choices': ['RBOD', 'JBOD', 'EBOD', 'virtual'],
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
            'choices': ['gallium', 'indium', 'virtual'],
            'help': 'Type of controller e.g {gallium | indium | virtual}'
        },
        'mode': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['primary', 'secondary'],
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
        self.machine_id = get_machine_id(node_id)
        self.enclosure_id = None
        self.mode = None

        # assign value to enclosure-id from /etc/enclosure-id if it exists
        if enc_file_path.exists():
            if Path(enc_file_path).stat().st_size != 0:
                with open(enc_file_path, "r") as file:
                    self.enclosure_id = file.read().replace('\n', '')

        self.refresh_conf_pillar_map()

    def refresh_conf_pillar_map(self):
        """updates values in the conf_pillar_map variable"""

        global conf_pillar_map
        conf_pillar_map = {
            'enclosure_id': (
                f'storage/{enc_num}/enclosure_id',
                f'server_node>{self.machine_id}>storage>enclosure_id'
            ),
            'user': (
                f'storage/{enc_num}/controller/user',
                f'storage_enclosure>{self.enclosure_id}>controller>user'
            ),
            'password': (
                f'storage/{enc_num}/controller/secret',
                f'storage_enclosure>{self.enclosure_id}>controller>secret'
            ),
            'ip': (
                f'storage/{enc_num}/controller/{self.mode}/ip',
                f'storage_enclosure>{self.enclosure_id}>controller>{self.mode}>ip'
            ),
            'port': (
                f'storage/{enc_num}/controller/{self.mode}/port',
                f'storage_enclosure>{self.enclosure_id}>controller>{self.mode}>port'
            ),
            'storage_type': (
                f'storage/{enc_num}/type',
                f'storage_enclosure>{self.enclosure_id}>type'
            ),
            'controller_type': (
                f'storage/{enc_num}/controller/type',
                f'storage_enclosure>{self.enclosure_id}>controller>type',
            ),
            'name': (
                f'storage/{enc_num}/name',
                f'storage_enclosure>{self.enclosure_id}>name',
            )
        }

    def store(self, key, value):
        """stores value in pillar and confstore"""

        self.logger.debug(f"Updating pillar with key:{conf_pillar_map[key][0]} and value:{value}")
        PillarSet().run(
            conf_pillar_map[key][0],
            value,
            targets=node_id,
            local=True
        )

        self.logger.debug(f"Updating Cortx Confstor with key:{conf_pillar_map[key][1]} and value:{value}")
        Conf.set(
            'node_info_index',
            conf_pillar_map[key][1],
            value
        )

    def store_in_file(self):
        """Writes enclosure id to file /etc/enclosure-id"""

        self.logger.debug(f"Writing storage enclosure_id to the file {enc_file_path}")
        file = open(enc_file_path, "w")
        file.write(self.enclosure_id + "\n")
        file.close()

    def run(self, **kwargs):

        user = kwargs.get('user')
        password = kwargs.get('password')
        ip = kwargs.get('ip')
        port = kwargs.get('port')

        name = kwargs.get('name')
        storage_type = kwargs.get('type')
        controller_type = kwargs.get('controller_type')
        self.mode = kwargs.get('mode')

        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )


        setup_type = Conf.get (
            f'server_node>{self.machine_id}>type'
        )

        if setup_type == "VM":
            if name or storage_type or controller_type:
                if not self.enclosure_id:
                    self.enclosure_id = "enc_" + self.machine_id
                    self.store_in_file()
                    self.store('enclosure_id', self.enclosure_id)

                self.refresh_conf_pillar_map()
                if name:
                    self.store('name', name)

                if storage_type:
                    self.store('storage_type', storage_type)

                if controller_type:
                    self.store('controller_type', controller_type)
            else:
                self.logger.error("Please provide values for name, type and controller_type")
                raise RuntimeError("Incomplete arguments provided")
        else:
            if user != None and password != None and ip != None and port != None:
                # fetch enclosure serial/id
                self.enclosure_id = EnclosureInfo(ip, user, password, port).get_enclosure_serial()
                self.mode = "primary"

                self.refresh_conf_pillar_map()

                # store enclosure_id
                self.store_in_file()
                self.store('enclosure_id', self.enclosure_id)

                # store user and password
                self.store('user', user)
                self.store('password', password)

                # store ip and port as primary
                self.store('ip', ip)
                self.store('port', port)
            else:
                self.refresh_conf_pillar_map()

                if name is not None:
                    if self.enclosure_id:
                        self.store('name', name)
                    else:
                        self.logger.error("Please set 'user, password, primary ip and port' first")
                        raise RuntimeError("Cannot set name before setting user, password, ip and port")

                if storage_type is not None:
                    if self.enclosure_id:
                        self.store('storage_type', storage_type)
                    else:
                        self.logger.error("Please set 'user, password, primary ip and port' first")
                        raise RuntimeError("Cannot set storage_type before setting user, password, ip and port")

                if controller_type is not None:
                    if self.enclosure_id:
                        self.store('controller_type', controller_type)
                    else:
                        self.logger.error("Please set 'user, password, primary ip and port' first")
                        raise RuntimeError("Cannot set storage_type before setting user, password, ip and port")

                if self.mode is not None:
                    if ip is None and port is None:
                        self.logger.exception(
                            f"Sub options for mode {self.mode} are missing"
                        )
                        raise RuntimeError('Please provide ip and/or port')

                    if self.enclosure_id:
                        if ip:
                            self.store('ip', ip)

                        if port:
                            self.store('port', port)
                    else:
                        self.logger.error(
                            "Enclosure ID is not set: Please provide user and password as well to set Enclosure ID"
                        )
                        raise RuntimeError("Incomplete arguments provided")

                if user is not None and password is not None:
                    if self.enclosure_id:
                        host = pillar_get(f"storage/{enc_num}/controller/primary/ip")[node_id][f'storage/{enc_num}/controller/primary/ip']
                        port = pillar_get(f"storage/{enc_num}/controller/primary/port")[node_id][f'storage/{enc_num}/controller/primary/port']

                        valid_connection_check = EnclosureInfo(host, user, password, port).connection_status()

                        if valid_connection_check:
                            self.store('user', user)
                            self.store('password', password)
                        else:
                            self.logger.error(
                                f"Cannot establish connection with controller using user={user} and password={password} as credentials"
                            )
                            raise ValueError("Invalid credentials provided")
                    else:
                        self.logger.error(
                            "Enclosure ID is not set: Please provide ip and port as well to set Enclosure ID"
                        )
                        raise RuntimeError("Incomplete arguments provided")

        Conf.save('node_info_index')
        self.logger.debug("Done")
