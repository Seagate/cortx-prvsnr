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
from cortx.utils.security.cipher import Cipher
from cortx_setup.commands.common_utils import get_machine_id
from cortx_setup.validate import ipv4
from cortx_setup.commands.common_utils import get_pillar_data
from provisioner.commands import PillarSet
from provisioner.salt import cmd_run, local_minion_id
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

conf_key_map = {}
pillar_key_map = {}

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
            'type': ipv4,
            'default': None,
            'optional': True,
            'help': 'IP address of the controller'
        },
        'port': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Port of the controller to connect to'
        },
        'cvg': {
            'type': int,
            'default': None,
            'optional': True,
            'help': 'cvg number'
        },
        'data-devices': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of data devices (Comma separated) e.g /dev/mapper/mpatha,/dev/mapper/mpathb'
        },
        'metadata-devices': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of metadata devices (Comma separated) e.g /dev/mapper/mpathf,/dev/mapper/mpathg'
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

        self.refresh_key_map()

    def refresh_key_map(self):
        """updates values in the pillar_key_map and conf_key_map dictionary"""

        global pillar_key_map
        global conf_key_map

        pillar_key_map = {
            'enclosure_id':     f'storage/{enc_num}/enclosure_id',
            'user':             f'storage/{enc_num}/controller/user',
            'password':         f'storage/{enc_num}/controller/secret',
            'ip':               f'storage/{enc_num}/controller/{self.mode}/ip',
            'port':             f'storage/{enc_num}/controller/{self.mode}/port',
            'storage_type':     f'storage/{enc_num}/type',
            'controller_type':  f'storage/{enc_num}/controller/type',
            'name':             f'storage/{enc_num}/name',
            'cvg':              f'cluster/{node_id}/storage/cvg',
            'data_devices':     f'cluster/{node_id}/storage/cvg/data_devices',
            'metadate_devices': f'cluster/{node_id}/storage/cvg/metadata_devices'
        }

        conf_key_map = {
            'enclosure_id':     f'server_node>{self.machine_id}>storage>enclosure_id',
            'user':             f'storage_enclosure>{self.enclosure_id}>controller>user',
            'password':         f'storage_enclosure>{self.enclosure_id}>controller>secret',
            'ip':               f'storage_enclosure>{self.enclosure_id}>controller>{self.mode}>ip',
            'port':             f'storage_enclosure>{self.enclosure_id}>controller>{self.mode}>port',
            'storage_type':     f'storage_enclosure>{self.enclosure_id}>type',
            'controller_type':  f'storage_enclosure>{self.enclosure_id}>controller>type',
            'name':             f'storage_enclosure>{self.enclosure_id}>name',
            'cvg':              f'server_node>{self.machine_id}>storage>cvg',
            'data_devices':     f'server_node>{self.machine_id}>storage>cvg>data_devices',
            'metadate_devices': f'server_node>{self.machine_id}>storage>cvg>metadata_devices'
        }

    def update_pillar_and_conf(self, key, value):
        """stores value in pillar and confstore"""

        self.logger.debug(f"Updating pillar with key:{pillar_key_map[key]} and value:{value}")
        PillarSet().run(
            pillar_key_map[key],
            value,
            targets=node_id,
            local=True
        )

        self.logger.debug(f"Updating Cortx Confstore with key:{conf_key_map[key]} and value:{value}")
        Conf.set(
            'node_info_index',
            conf_key_map[key],
            value
        )

    def store_in_file(self):
        """Writes enclosure id to file /etc/enclosure-id"""

        self.logger.debug(f"Writing storage enclosure_id to the file {enc_file_path}")
        file = open(enc_file_path, "w")
        file.write(self.enclosure_id)
        file.close()

    def encrypt_password(self, password):
        """Returns encrypted password as string"""

        cipher_key = Cipher.generate_key(self.enclosure_id, "storage")
        return str(
            Cipher.encrypt(
                cipher_key, bytes(password, 'utf-8')
            ),
            'utf-8'
        )

    def run(self, **kwargs):

        user = kwargs.get('user')
        password = kwargs.get('password')
        ip = kwargs.get('ip')
        port = kwargs.get('port')

        name = kwargs.get('name')
        storage_type = kwargs.get('type')
        controller_type = kwargs.get('controller_type')
        self.mode = kwargs.get('mode')

        cvg = kwargs.get('cvg')
        data_devices = kwargs.get('data_devices')
        metadata_devices = kwargs.get('metadata_devices')

        Conf.load(
            'node_info_index',
            f'json://{prvsnr_cluster_path}'
        )

        setup_type = Conf.get (
            'node_info_index',
            f'server_node>{self.machine_id}>type'
        )
        if setup_type == None:
            self.logger.error("Setup type is not set, please set the"
            " setup type and try again, run following command to set"
            " the setup type: 'cortx_config server config type <VM|HW>'"
            )
            raise RuntimeError("Could not find the setup type in conf store")


        if setup_type == "VM":
            if (
                name
                or storage_type
                or controller_type
                or cvg
                or data_devices
                or metadata_devices
            ):
                if not self.enclosure_id:
                    self.enclosure_id = "enc_" + self.machine_id
                    self.refresh_key_map()
                    self.store_in_file()
                    self.update_pillar_and_conf(
                        'enclosure_id',
                        self.enclosure_id
                    )

                if name:
                    self.update_pillar_and_conf('name', name)

                if storage_type != "virtual":
                    self.logger.error(
                        "Storage type needs to be 'virtual' for VM")
                    raise ValueError("Incorrect argument value provided")
                else:
                    self.update_pillar_and_conf('storage_type', storage_type)

                if controller_type != "virtual":
                    self.logger.error(
                        "Controller type needs to be 'virtual' for VM")
                    raise ValueError("Incorrect argument value provided")
                else:
                    self.update_pillar_and_conf(
                        'controller_type',
                        controller_type
                    )

                if cvg > 1:
                    self.logger.error(
                        "The value of CVG has to be either 0 or 1")
                    raise ValueError("Incorrect argument value provided")
                else:
                    self.update_pillar_and_conf('cvg', cvg)

                if data_devices:
                    ddevices = data_devices.split(",")
                    for device in ddevices:
                        cmd_run(f"ls {device}", targets=node_id)

                    self.update_pillar_and_conf('data_devices', ddevices)

                if metadata_devices:
                    mdevices = data_devices.split(",")
                    for device in mdevices:
                        cmd_run(f"ls {device}", targets=node_id)

                    self.update_pillar_and_conf('metadata_devices', mdevices)

            else:
                self.logger.error(
                    "Please provide values for name, type and controller_type,"
                    " cvg, data_devices, metadata_devices"
                )
                raise RuntimeError("Incomplete arguments provided")
        else:
            if user != None and password != None and ip != None and port != None:
                # fetch enclosure serial/id
                self.enclosure_id = EnclosureInfo(
                                        ip,
                                        user,
                                        password,
                                        port
                                    ).fetch_enclosure_serial()
                self.mode = "primary"

                self.refresh_key_map()

                # store enclosure_id
                self.store_in_file()
                self.update_pillar_and_conf('enclosure_id', self.enclosure_id)

                # store user
                self.update_pillar_and_conf('user', user)

                # encrypt password and store
                password = self.encrypt_password(password)
                self.update_pillar_and_conf('password', password)

                # store ip and port as primary
                self.update_pillar_and_conf('ip', ip)
                self.update_pillar_and_conf('port', port)
            else:
                self.refresh_key_map()

                if name is not None:
                    if self.enclosure_id:
                        self.update_pillar_and_conf('name', name)
                    else:
                        self.logger.error("Enclosure ID is not set"
                            "Run following command to set the enclosure id:"
                            "cortx_setup storage config --user <user>"
                            " --password <passwd> --ip <ip> --port <port>")
                        raise RuntimeError(
                            "Cannot set enclosure name without enclosure id"
                        )

                if storage_type is not None:
                    if self.enclosure_id:
                        if storage_type == "virtual":
                            self.logger.error(
                            "Storage type can not be 'virtual' for HW")
                            raise ValueError("Incorrect argument value provided")
                        else:
                            self.update_pillar_and_conf(
                                'storage_type',
                                storage_type
                            )
                    else:
                        self.logger.error("Enclosure ID is not set"
                            "Run following command to set the enclosure id:"
                            "cortx_setup storage config --user <user>"
                            " --password <passwd> --ip <ip> --port <port>")
                        raise RuntimeError(
                            "Cannot set enclosure type without enclosure id"
                        )

                if controller_type is not None:
                    if self.enclosure_id:
                        if controller_type == "virtual":
                            self.logger.error(
                            "Controller type can not be 'virtual' for HW")
                            raise ValueError("Incorrect argument value provided")
                        else:
                            self.update_pillar_and_conf(
                                'controller_type',
                                controller_type
                            )
                    else:
                        self.logger.error("Enclosure ID is not set"
                            "Run following command to set the enclosure id:"
                            "cortx_setup storage config --user <user>"
                            " --password <passwd> --ip <ip> --port <port>")
                        raise RuntimeError(
                            "Cannot set controller type without enclosure id"
                        )

                if self.mode is not None:
                    if ip is None and port is None:
                        self.logger.exception(
                            f"Sub options for mode {self.mode} are missing"
                        )
                        raise RuntimeError('Please provide ip and/or port')

                    if self.enclosure_id:
                        if ip:
                            self.update_pillar_and_conf('ip', ip)

                        if port:
                            self.update_pillar_and_conf('port', port)
                    else:
                        self.logger.error("Enclosure ID is not set"
                            "Run following command to set the enclosure id:"
                            "cortx_setup storage config --user <user>"
                            " --password <passwd> --ip <ip> --port <port>")
                        raise RuntimeError(
                            "Cannot set mode, ip and port without enclosure id"
                        )

                if user is not None and password is not None:
                    if self.enclosure_id:
                        host = get_pillar_data(
                            f"storage/{enc_num}/controller/primary/ip"
                            )[node_id][f'storage/{enc_num}/controller/primary/ip']
                        port = get_pillar_data(
                            f"storage/{enc_num}/controller/primary/port"
                            )[node_id][f'storage/{enc_num}/controller/primary/port']

                        valid_connection_check = EnclosureInfo(
                                                    host,
                                                    user,
                                                    password,
                                                    port
                                                ).connection_status()

                        if valid_connection_check:
                            self.update_pillar_and_conf('user', user)
                            self.update_pillar_and_conf('password', password)
                        else:
                            self.logger.error(
                                f"Could not establish connection with"
                                " controller with provided credentials"
                            )
                            raise ValueError("Invalid credentials provided")
                    else:
                        self.logger.error(
                            "Enclosure ID is not set:"
                            " Please provide controller ip and port to fetch"
                            " the enclosure id"
                        )
                        raise RuntimeError("Incomplete arguments provided")

                if cvg > 1:
                    self.logger.error(
                        "The value of CVG has to be either 0 or 1")
                    raise ValueError("Incorrect argument value provided")
                else:
                    self.update_pillar_and_conf('cvg', cvg)

                if data_devices:
                    ddevices = data_devices.split(",")
                    for device in ddevices:
                        cmd_run(f"ls {device}", targets=node_id)

                    self.update_pillar_and_conf('data_devices', ddevices)

                if metadata_devices:
                    mdevices = data_devices.split(",")
                    for device in mdevices:
                        cmd_run(f"ls {device}", targets=node_id)

                    self.update_pillar_and_conf('metadata_devices', mdevices)


        Conf.save('node_info_index')
        self.logger.debug("Done")
