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

import logging
import os
import subprocess
from scripts.utils.common import run_subprocess_cmd
from messages.user_messages import *

logger = logging.getLogger(__name__)

class HardwareValidations():

    def __init__(self):
        ''' Validations for pre-factory HW steps
        '''
        pass

    def mlnx_ofed_installed(self):
        ''' Validations for Mellanox drivers
        '''
        cmd = "yum list yum list mlnx-ofed-all | grep mlnx-ofed*"
        common_response = run_subprocess_cmd(cmd)
        print ("UTIL: ", common_response)
        return common_response

    def mlnx_hca_present(self):
        ''' Validations for Mellanox drivers
        '''
        cmd = "lspci -nn | grep 'Mellanox Technologies'"
        common_response = run_subprocess_cmd(cmd, shell=True)
        return common_response

    def mlnx_hca_req_ports(self):
        ''' Validations for Mellanox drivers
        '''
        cmd = "lspci -nn | grep 'Mellanox Technologies' | wc -l"
        # TO DO: Check os function result
        common_response = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        return common_response

    def lsb_hba_present(self):
        ''' Validations for LUNs
        '''
        cmd = "lspci -nn | grep 'SCSI'"
        common_response = run_subprocess_cmd(cmd, shell=True)
        return common_response

    def lsb_hba_req_ports(self):
        ''' Validations for LUNs
        '''
        cmd = "ls /sys/class/scsi_host/ | wc -l"
        # TO DO: Check os function result
        common_response = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        return common_response
