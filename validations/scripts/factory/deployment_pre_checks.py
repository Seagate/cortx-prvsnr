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

import configparser
import logging
import subprocess
import time
import yaml
import os
import os.path
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/utils")

import config
import common
from common import run_subprocess_cmd

from pathlib import Path, PosixPath
from typing import (
    Tuple,
    Union,
    Optional,
    List
)

from errors import (
    ProvisionerError, SubprocessCmdError
)

logger = logging.getLogger(__name__)

# NOTE-1: Have not raised Exception in case of validation failure
# As it may stop the flow of other checks. 
# NOTE-2: Returning a Generic output for all validations
# To make it easy to parse in main registry file

class PreFactoryValidations():

    def __init__(self):
        ''' Validations for pre-factory deployment
        '''
        pass

    def mlnx_ofed_installed(self):
        ''' Validations for Mellanox drivers
        '''
        cmd = "yum list yum list mlnx-ofed-all | grep mlnx-ofed*"
        # cmd = "ibv_devinfo"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: Mellanox OFED Is Installed" }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: Mellanox OFED Is Not Installed" }


    def mlnx_hca_present(self):
        ''' Validations for Mellanox drivers
        '''
        cmd_present = "lspci -nn | grep 'Mellanox Technologies'"
        response = run_subprocess_cmd(cmd_present)
        if response[0] == 0:
            cmd_ports = "lspci -nn | grep 'Mellanox Technologies' | wc -l"
            resp = run_subprocess_cmd(cmd_ports)
            if resp[1] != 0:
                return {"ret_code": response[0],
                        "response": response[1],
                        "error_msg": response[2],
                        "message": "CHECK: Mellanox HCA Present And Has Required Number Of Ports"}
            else:
                return {"ret_code": response[0],
                        "response": response[1],
                        "error_msg": response[2],
                        "message": "ERROR: Mellanox HCA Present But Does Not Have Required Number of ports"}
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: Mellanox HCA Not Present"}

    def lsb_hba_present(self):
        ''' Validations for LUNs
        '''
        cmd_present = "lspci -nn | grep 'SCSI'"
        response = run_subprocess_cmd(cmd_present)
        if response[0] == 0: 
            cmd_ports = "ls /sys/class/scsi_host/ | wc -l"
            resp = run_subprocess_cmd(cmd_ports)
            if resp[1] != 0:
                return {"ret_code": response[0],
                        "response": response[1],
                        "error_msg": response[2],
                        "message": "CHECK: LSB HBA Present And Has Required Number Of Ports"}
            else:
                return {"ret_code": response[0],
                        "response": response[1],
                        "error_msg": response[2],
                        "message": "ERROR: LSB HBA Present But Does Not Have Required Number of ports"}
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: LSB HBA Not Present"}

    def volumes_accessible(self):
        ''' Validations for Enclosure Volumes
        '''
        cmd = "lsblk -S && ls -1 /dev/disk/by-id/scsi-*"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: Enclosure Volumes Are Accessible From Both Servers" }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: Enclosure Volumes Are Not Accessible"}

    def volumes_mapped(self):
        ''' Validations for Enclosure Volumes
        '''
        cmd_priority_50 = "multipath -ll | grep prio=50 | wc -l"
        cmd_priority_10 = "multipath -ll | grep prio=10 | wc -l"
        response_50 = run_subprocess_cmd(cmd_priority_50)
        response_10 = run_subprocess_cmd(cmd_priority_10)
        if response_50[0] and response_10[0] == "16":
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: Enclosure Volumes Are Mapped To Both Controllers" }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: Enclosure Volumes Not Mapped to Controllers. Run rescan_scsi_bus.sh file"}

#def main():
#    pre_deploy = PreFactoryValidations()
#    pre_deploy.mlnx_ofed_installed()
#
#if __name__ == '__main__':
#    main()
