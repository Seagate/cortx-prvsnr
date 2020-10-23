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
import sys
from scripts.utils.hardware import HardwareValidations
from scripts.utils.storage import StorageValidations
from messages.user_messages import *
logger = logging.getLogger(__name__)

class PreFlightValidationsCall():

    def __init__(self):
        ''' Validations for factory HW steps
        '''
        self.hw = HardwareValidations()
        self.storage = StorageValidations()
        pass

    def check_mlnx_ofed_installed(self):
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = self.hw.mlnx_ofed_installed()
        if res[0] == 0:
            response["message"]= str(MLNX_INSTALL_CHECK)
        else:
            response["message"]= str(MLNX_INSTALL_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_mlnx_hca_present(self):
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = self.hw.mlnx_hca_present()
        if res[0] == 0:
            response["message"]= str(MLNX_HCA_CHECK)
        else:
            response["message"]= str(MLNX_HCA_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_mlnx_hca_req_ports(self):
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = self.hw.mlnx_hca_req_ports()
        if res[0] != 0:
            response["message"]= str(MLNX_HCA_PORTS_CHECK)
            response["ret_code"]= 0
            response["response"]= int(res)
            response["error_msg"]= "NULL"
        else:
            response["message"]= str(MLNX_HCA_PORTS_ERROR)
            response["ret_code"]= 1
            response["response"]= int(res)
            response["error_msg"]= res
        return response


    def check_lsb_hba_present(self):
        ''' Validations for LUNs
        '''
        response = {}
        res = self.hw.lsb_hba_present()
        if res[0] == 0:
            response["message"]= str(LSB_HBA_CHECK)
        else:
            response["message"]= str(LSB_HBA_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_lsb_hba_req_ports(self):
        ''' Validations for LUNs
        '''
        response = {}
        res = self.hw.lsb_hba_req_ports()
        if res[0] != 0:
            response["message"]= str(LSB_HBA_PORTS_CHECK)
            response["ret_code"]= 0
            response["response"]= int(res)
            response["error_msg"]= "NULL"
        else:
            response["message"]= str(LSB_HBA_PORTS_ERROR)
            response["ret_code"]= 1
            response["response"]= int(res)
            response["error_msg"]= res
        return response

    def check_volumes_accessible(self):
        ''' Validations for Enclosure Volumes
        '''
        response = {}
        res = self.storage.volumes_accessible()
        if not res[0]:
            response["message"]= str(VOLUMES_ACCESSIBLE_CHECK)
        else:
            response["message"]= str(VOLUMES_ACCESSIBLE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response


    def check_volumes_mapped(self):
        ''' Validations for Enclosure Volumes
        '''
        response = {}
        res = self.storage.volumes_mapped()
        if "16" in (str(res[0]) and str(res[1])):
            response["message"]= str(VOLUMES_MAPPED_TO_CNTRLRS_CHECK)
            response["ret_code"]= 0
            response["response"]= str(res)
            response["error_msg"]= "NULL"
        else:
            response["message"]= str(VOLUMES_MAPPED_TO_CNTRLRS_ERROR)
            response["ret_code"]= 1
            response["response"]= str(res)
            response["error_msg"]= "Error"
        return response
