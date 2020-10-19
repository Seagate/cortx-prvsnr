#!/usr/bin/env python
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
import ..utils.pacemaker as pacemaker 
from .. .messages.user_messages import *
logger = logging.getLogger(__name__)

class PreFactoryValidationsCall():

    def __init__(self):
        ''' Validations for pre-factory deployment
        '''
        pass

    @staticmethod
    def check_mlnx_ofed_installed():
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = pre_deployment.mlnx_ofed_installed()
        if res[0] == 0:
            response["message"]= str(MLNX_INSTALL_CHECK)
        else:
            response["message"]= str(MLNX_INSTALL_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    @staticmethod
    def check_mlnx_hca_present():
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = pre_deployment.mlnx_hca_present()
        if res[0] == 0:
            response["message"]= str(MLNX_HCA_CHECK)
        else:
            response["message"]= str(MLNX_HCA_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response


    @staticmethod
    def check_mlnx_hca_req_ports():
        ''' Validations for Mellanox drivers
        '''
        response = {}
        res = pre_deployment.mlnx_hca_req_ports()
        if res[0] != 0:
            response["message"]= str(MLNX_HCA_PORTS_CHECK)
        else:
            response["message"]= str(MLNX_HCA_PORTS_ERROR)
        # TO DO: Response parsing based on common os function 
        response["ret_code"]= "0"
        response["response"]= int(res)
        response["error_msg"]= "NULL"
        return response


    @staticmethod
    def check_lsb_hba_present():
        ''' Validations for LUNs
        '''
        response = {}
        res = pre_deployment.lsb_hba_present()
            response["message"]= str(LSB_HBA_CHECK)
        else:
            response["message"]= str(LSB_HBA_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    @staticmethod
    def check_lsb_hba_req_ports():
        ''' Validations for LUNs
        '''
        response = {}
        res = pre_deployment.lsb_hba_req_ports()
        if res[0] != 0:
            response["message"]= str(LSB_HBA_PORTS_CHECK)
        else:
            response["message"]= str(LSB_HBA_PORTS_ERROR)
        # TO DO: Response parsing based on common os function 
        response["ret_code"]= "0"
        response["response"]= int(res)
        response["error_msg"]= "NULL"
        return response

    @staticmethod
    def check_volumes_accessible():
        ''' Validations for Enclosure Volumes
        '''
        response = {}
        res = pre_deployment.volumes_accessible()
        res = run_subprocess_cmd(cmd, shell=True)
        if res[0] == 0:
            response["message"]= str(VOLUMES_ACCESSIBLE_CHECK)
        else:
            response["message"]= str(VOLUMES_ACCESSIBLE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    @staticmethod
    def check_volumes_mapped():
        ''' Validations for Enclosure Volumes
        '''
        response = {}
        res = pre_deployment.volumes_mapped()
        print ("RESPONSE 10: " , res)
        if res == "16":
            response["message"]= str(VOLUMES_MAPPED_TO_CNTRLRS_CHECK)
        else:
            response["message"]= str(VOLUMES_MAPPED_TO_CNTRLRS_ERROR)
        response["ret_code"]= "0"
        response["response"]= int(res)
        response["error_msg"]= "NULL"
        return response
