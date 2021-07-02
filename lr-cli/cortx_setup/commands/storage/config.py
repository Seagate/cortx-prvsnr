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
from collections import OrderedDict
from provisioner.commands import PillarSet
from provisioner.salt import cmd_run, local_minion_id
from provisioner.values import MISSED
from .enclosure_info import EnclosureInfo
from cortx_setup.commands.common_utils import get_pillar_data
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
    $ cortx_setup storage config --name <enclosure-name> --type {RBOD|JBOD|EBOD|virtual}
    $ cortx_setup storage config --controller {gallium|indium|virtual} --mode {primary|secondary}
    $ cortx_setup storage config --cvg {0|1} --metadata_devices <device list> --data_devices <data_devices>
    e.g.
    $ cortx_setup storage config --controller gallium --mode primary --ip <ip-address> --port <port-number> --user <user> --password <paasword>
    $ cortx_setup storage config --controller gallium --mode secondary --ip <ip-address> --port <port-number> --user <user> --password <paasword>

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
        'controller': {
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
            'default': -1,
            'optional': True,
            'help': 'Cylinder Volume Group number.'
        },
        'data_devices': {
            'type': str,
             'optional': True,
            'help': 'List of data devices (Comma separated) e.g /dev/mapper/mpatha,/dev/mapper/mpathb'
        },
        'metadata_devices': {
            'type': str,
            'optional': True,
            'help': 'List of metadata devices (Comma separated) e.g /dev/mapper/mpathf,/dev/mapper/mpathg'
        }
    }

    def __init__(self):
        super().__init__()
        self.machine_id = None
        self.enclosure_id = None
        self.mode = None
        self.cvg_count = -1

        # assign value to enclosure-id from /etc/enclosure-id if it exists
        if enc_file_path.exists():
            if Path(enc_file_path).stat().st_size != 0:
                with open(enc_file_path, "r") as file:
                    self.enclosure_id = file.read().replace('\n', '')


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
            'cvg':              f'cluster/{node_id}/storage/cvg_count',
            'cvg_devices':      f'cluster/{node_id}/storage/cvg'
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
            'cvg':              f'server_node>{self.machine_id}>storage>cvg_count',
            'cvg_devices':      f'server_node>{self.machine_id}>storage>cvg'
        }

    def update_pillar_and_conf(self, key, value):
        """stores value in pillar and confstore"""

        self.logger.debug(f"Updating pillar with key:{pillar_key_map[key]} and value:{value}")
        PillarSet().run(
            pillar_key_map[key],
            value,
            local=True
        )

        if(key=='password'):
            value = self.encrypt_password(value)

        if key == "cvg":
            value = str(value)

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
        # valid combinations for cortx_setup storage config
        # Hardware
        # 1.  --controller galium --mode primary --ip <> --port <> --user <> --password <>
        # 2.  --name enc_rack1 --type RBOD
        # 3.  --mode primary --ip <> --port <>
        # 4.  --user <> --password
        # 5.  --controller galium
        # 6.  --cvg 0 --data_devices /dev/sdb,/dev/sdc --metadata_devices /dev/sdd
        # VM
        # 1.  --controller virtual --mode primary --ip <> --port <> --user <> --password <>
        # 2.  --name virtual_rack1 --type virtual
        # 3.  --cvg 0 --data_devices /dev/sdb,/dev/sdc --metadata_devices /dev/sdd

        user = kwargs.get('user')
        password = kwargs.get('password')
        ip = kwargs.get('ip')
        port = kwargs.get('port')

        name = kwargs.get('name')
        storage_type = kwargs.get('type')
        controller_type = kwargs.get('controller')
        self.mode = kwargs.get('mode')
        cred_validation = False
        self.cvg_count = int(kwargs.get('cvg'))
        data_devices = []
        input_data_devices = kwargs.get('data_devices')
        if input_data_devices:
            data_devices = input_data_devices.split(",")
        metadata_devices = []
        input_metadata_devices = kwargs.get('metadata_devices')
        if input_metadata_devices:
            metadata_devices = input_metadata_devices.split(",")

        self.machine_id = get_machine_id(node_id)
        self.refresh_key_map()

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
            " setup type and try again")
            self.logger.error("Run following command to set the setup type"
            ": 'cortx_setup server config type <VM|HW>'"
            )
            raise RuntimeError("Could not find the setup type in conf store")
    
        if self.enclosure_id is None:
            self.enclosure_id =  get_pillar_data(pillar_key_map['enclosure_id'])
            if self.enclosure_id is MISSED:
                self.enclosure_id= None
            self.refresh_key_map()
            self.logger.debug(f"enclosure id: {self.enclosure_id}")
            if self.enclosure_id is None and setup_type == "VM":
                self.enclosure_id = "enc_" + self.machine_id
                self.refresh_key_map()
                self.store_in_file()
                self.update_pillar_and_conf('enclosure_id', self.enclosure_id)

        ### THE "mode" SHOULD ALWAYS BE THE FIRST CHECK, DO NOT CHANGE THIS SEQ ###
        if self.mode is not None:
            if ip is None or port is None:
                # mandetory sub options for mode (ip and port) are missing.
                self.logger.exception(
                    f"Mandatory sub options for mode- ip & password are missing"
                )
                raise RuntimeError('Please provide ip and port')
            # Algorithm to update ip and port the enclosure id is needed.
            # if enclosure_id and user and password
            #    reset the enclosure id fetched from confstore
            #    this is to force fetch the enclosure if with
            #    current set of input parameters - user, passwd, ip, port.
            # if not self.enclosure_id:
            #     if hw:
            #         if user and password:
            #             #fetch enclosure id and store in confstore
            #         else:
            #             #error
            # if self.enclosure_id:
            #     # store ip and port in confstore
            #     if user and password:
            #         # store in confstore
            if (
                self.enclosure_id is not None
                and user is not None
                and password is not None
                and setup_type == "HW"
            ):
                # user has provided all the parameters that fetches the
                # enclosure id, so reset the enclosure id read from the
                # confstore and fetch it again with the current set of
                # parameters
                self.enclosure_id = None

            if self.enclosure_id is None:
                if setup_type == "HW":
                    # Fetch enclosure id if the user & password are also provided
                    if (user != None and password != None):
                        self.enclosure_id = EnclosureInfo(
                                                ip,
                                                user,
                                                password,
                                                port
                                            ).fetch_enclosure_serial()
                        if self.enclosure_id:
                            # store enclosure_id in /etc/enclosure-id
                            self.store_in_file()
                            self.refresh_key_map()
                            self.update_pillar_and_conf('enclosure_id', self.enclosure_id)
                            cred_validation = True
                        else:
                            self.logger.exception("Could not fetch the enclosure id")
                            raise RuntimeError(
                                'Please check if credentials, ip & port provided'
                                ' are correct.'
                            )
                    else:
                        self.logger.exception(
                            "Could not update ip and port in Cortx configuration"
                            " without enclosure id. Please provide user, password,"
                            " ip and port together to fetch the enclosure id from"
                            " attached enclosure.")
                        raise RuntimeError(
                            'Incomplete set of arguments provided'
                        )
            if self.enclosure_id is not None:
                if setup_type == "VM":
                    self.logger.warning("WARNING: This is VM")
                    self.logger.warning(
                        "WARNING: Adding ip and port in confstore without validation"
                    )
                if setup_type == "HW" and not cred_validation:
                    self.logger.warning(
                        "WARNING:  Adding ip and port in confstore without"
                        " validation To force the validation, please run:"
                        " cortx_setup storage config --controller <type>"
                        " --mode primary --ip <ip> --port <port>"
                        " --user <user> --password <password>"
                    )
                self.update_pillar_and_conf('ip', ip)
                self.update_pillar_and_conf('port', port)
            else:
                self.logger.exception(
                    "Could not update ip and port without enclosure id"
                    "Please provide user, password, ip & port together")
                raise RuntimeError(
                    'Incomplete set of arguments provided'
                )

        if user is not None or password is not None:
            if (user is None) or (password is None):
                self.logger.error(
                    f"Please provide 'user' and 'passowrd' together")
                raise RuntimeError("Imcomplete arguments provided")
            if self.enclosure_id is not None and setup_type == "VM":
                self.logger.warning("WARNING: This is VM")
                self.logger.warning(
                    "WARNING: Adding user and password in confstore"
                    " without validation")
                self.update_pillar_and_conf('user', user)
                self.update_pillar_and_conf('password', password)
            elif self.enclosure_id is not None and setup_type == "HW":
                # Store user and password only after validation
                # Skip the validation if enclosure id was fetched
                #  using the same credentials
                if not cred_validation:
                    # Read ip & port from Pillar and validate by logging
                    # in to enclosure with user, passwd, ip and port
                    self.logger.debug("Validating the user and password provided")
                    host_in_pillar = get_pillar_data(
                        f"storage/{enc_num}/controller/primary/ip")
                    port_in_pillar = get_pillar_data(
                        f"storage/{enc_num}/controller/primary/port")
                    if not host_in_pillar or not port_in_pillar:
                        self.logger.error(
                            f"Could not read controller ip and secret from pillar")
                        raise RuntimeError("Could not validate user and password")
                    valid_connection_check = EnclosureInfo(
                                                host_in_pillar,
                                                user,
                                                password,
                                                port_in_pillar
                                            ).connection_status()
                    if not valid_connection_check:
                        self.logger.error(
                            f"Could not establish connection with"
                            " controller with provided credentials"
                        )
                        raise ValueError("Invalid credentials provided")
                self.update_pillar_and_conf('user', user)
                self.update_pillar_and_conf('password', password)
            else:
                self.logger.error(f"Enclosure ID is not set\n"
                    "Run following command to set the enclosure id:"
                    "cortx_setup storage config --user <user>"
                    " --password <passwd> --ip <ip> --port <port>")
                raise RuntimeError(
                    "Cannot set mode, ip and port without enclosure id"
                )

        if ip is not None or port is not None:
            if self.mode is None:
                self.logger.exception(
                    f"mode is missing, please provide --mode argument"
                )
                raise RuntimeError("Incomplete arguments provided")
            else:
                # This is already handled in 'mode' case
                pass

        if controller_type is not None:
            valid_ctrl_type = ['gallium', 'indium']
            if setup_type == "HW" and controller_type not in valid_ctrl_type:
                self.logger.error(
                "Invalid controller provided, please provide the"
                " supported controller type")
                raise ValueError("Incorrect argument value provided")
            if setup_type == "VM" and controller_type != "virtual":
                self.logger.error(
                "Controller must be 'virtual' for VM")
                raise ValueError("Incorrect argument value provided")
            if self.enclosure_id is None:
                self.logger.error(f"Enclosure ID is not set\n"
                    "Run following command to set the enclosure id:"
                    "cortx_setup storage config --controller primary --user"
                    " <user> --password <passwd> --ip <ip> --port <port>")
                raise RuntimeError(
                    "Cannot set controller type without enclosure id"
                )
            # all checks are good, update confstore and pillar
            self.update_pillar_and_conf(
                'controller_type',
                controller_type
            )

        if name is not None or storage_type is not None:
            if (name and not storage_type) or (storage_type and not name):
                self.logger.error(
                    f"Please provide 'name' and 'type' together")
                raise RuntimeError("Imcomplete arguments provided")
            if self.enclosure_id is not None:
                self.update_pillar_and_conf('name', name)
                supported_type = ['RBOD', 'JBOD', 'EBOD']
                if setup_type == "HW" and storage_type not in supported_type:
                    self.logger.error(
                    "Invalid type provided, please provide the"
                    " supported storage type")
                    raise ValueError("Incorrect argument value provided")
                if setup_type == "VM" and storage_type != "virtual":
                    self.logger.error(
                    "Storage type must be 'virtual' for VM")
                    raise ValueError("Incorrect argument value provided")
            else:
                self.logger.error(f"Enclosure ID is not set\n"
                    "Run following command to set the enclosure id:"
                    "cortx_setup storage config --user <user>"
                    " --password <passwd> --ip <ip> --port <port>")
                raise RuntimeError(
                    "Cannot set enclosure type without enclosure id"
                )
            # all clear, update name and type in confstore and pillar
            self.update_pillar_and_conf('name', name)
            self.update_pillar_and_conf(
                'storage_type',
                storage_type
            )

        if self.cvg_count != -1:
            if not data_devices or not metadata_devices:
                self.logger.error(
                    "The parameters data_devices and metadata_devices"
                    " are missing")
                raise RuntimeError("Incomplete arguments provided")

            current_cvg_count = Conf.get (
                'node_info_index',
                f'server_node>{self.machine_id}>storage>cvg_count'
            )
            if not current_cvg_count:
                current_cvg_count = 0

            cvg_list = get_pillar_data('cluster/srvnode-0/storage/cvg')
            if not cvg_list or cvg_list is MISSED:
                cvg_list = []
            elif isinstance(cvg_list[0], OrderedDict):
                for i,key in enumerate(cvg_list):
                    cvg_list[i] = dict(key)
            if data_devices:
                self.logger.debug(f"data_devices: {data_devices}")
                for device in data_devices:
                    try:
                        cmd_run(f"ls {device}", targets=node_id)
                    except:
                        raise ValueError(
                            f"Validation for data device {device} failed\n"
                            "Please provide the correct device")
            if metadata_devices:
                self.logger.debug(f"metadata_devices: {metadata_devices}")
                for device in metadata_devices:
                    try:
                        cmd_run(f"ls {device}", targets=node_id)
                    except:
                        raise ValueError(
                                f"Validation for data device {device} failed\n"
                                "Please provide the correct device")
            cvg_list.insert(self.cvg_count, {'data_devices': data_devices, 'metadata_devices': metadata_devices})
            self.cvg_count = self.cvg_count + 1
            self.update_pillar_and_conf('cvg', self.cvg_count)
            self.update_pillar_and_conf('cvg_devices', cvg_list)

        Conf.save('node_info_index')
        self.logger.debug("Done")

