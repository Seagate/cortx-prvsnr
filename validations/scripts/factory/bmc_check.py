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
import ..utils.bmc as bmc
from .. .messages.user_messages import *
from ..utils.network_connectivity_checks import NetworkValidations
logger = logging.getLogger(__name__)

class BMCValidationsCall():

    def __init__(self):
        ''' Validations for BMC steps
        '''
        pass

    def ping_bmc():
        ''' Ping BMC IP
        '''
        response = {}
        res_ip = bmc.get_bmc_ip()
        if not res_ip[0]:
            ping_check = NetworkValidations.check_ping(res_ip)
            if ping_check[0] == 0:
                response["message"]= str(BMC_ACCESSIBLE_CHECK)
            else:
                response["message"]= str(BMC_ACCESSIBLE_ERROR)
        else:
            response["message"]= str(BMC_IP_ERROR)
        response["ret_code"]= ping_check[0]
        response["response"]= ping_check[1]
        response["error_msg"]= ping_check[2]
        return response

    def check_bmc_accessible():
        ''' Validations for BMC accessibility
        '''
        response = {}
        bmc_res = bmc.bmc_accessible()
        bmc_ping_res = ping_bmc() 
        if bmc_res[0] and bmc_ping_res[0] == 0:
            response["message"]= str(BMC_ACCESSIBLE_CHECK)
        else:
            response["message"]= str(BMC_ACCESSIBLE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response