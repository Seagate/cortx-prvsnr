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
from ..utils.hardware import HardwareValidations as hw
from .. .messages.user_messages import *
logger = logging.getLogger(__name__)

class HardwareValidationsCall():

    def __init__(self):
        ''' Validations for factory HW steps
        '''
        pass

    def check_mlnx_ofed_installed(self):
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = hw.mlnx_ofed_installed()
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
        res = hw.mlnx_hca_present()
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
        res = hw.mlnx_hca_req_ports()
        if res[0] != 0:
            response["message"]= str(MLNX_HCA_PORTS_CHECK)
        else:
            response["message"]= str(MLNX_HCA_PORTS_ERROR)
        # TO DO: Response parsing based on common os function 
        response["ret_code"]= "0"
        response["response"]= int(res)
        response["error_msg"]= "NULL"
        return response


    def check_lsb_hba_present(self):
        ''' Validations for LUNs
        '''
        response = {}
        res = hw.lsb_hba_present()
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
        res = hw.lsb_hba_req_ports()
        if res[0] != 0:
            response["message"]= str(LSB_HBA_PORTS_CHECK)
        else:
            response["message"]= str(LSB_HBA_PORTS_ERROR)
        # TO DO: Response parsing based on common os function 
        response["ret_code"]= "0"
        response["response"]= int(res)
        response["error_msg"]= "NULL"
        return response