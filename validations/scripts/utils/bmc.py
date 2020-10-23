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
import os, subprocess
from scripts.utils.common import run_subprocess_cmd
from scripts.utils.pillar_get import PillarGet
from messages.user_messages import *
from scripts.utils.network_connectivity_checks import NetworkValidations

logger = logging.getLogger(__name__)

class BMCValidations():

    def __init__(self):
        ''' Validations for BMC steps
        '''
        pass

    def get_bmc_ip(self):
        '''
        Get BMC IP along with status of command
        '''
        common_response = {}
        node_res = PillarGet.get_pillar("cluster:node_list")
        if not node_res['ret_code']:
            nodes = node_res['response']
            for node in nodes:
                common_response["response"] = PillarGet.get_pillar(f"cluster:{node}:bmc:ip")
        # TO TEST
        else:
            common_response["response"] = "BMC IP Not Found"
        common_response["ret_code"]= node_res[0]
        common_response["error_msg"]= node_res[2]
        return common_response

    def ping_bmc(self):
        ''' Ping BMC IP
        '''
        response = {}
        res_ip = self.get_bmc_ip()
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

    def bmc_accessible(self):
        ''' Validations for BMC accessibility
        '''
        cmd = "ipmitool chassis status | grep 'System Power'"
        common_response = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        print (common_response)
        #print (common_response)
        bmc_ping_res = self.ping_bmc()
        if ("on" in common_response) and (bmc_ping_res[0]) == 0:
            response["message"]= str(BMC_ACCESSIBLE_CHECK)
        else:
           response["message"]= str(BMC_ACCESSIBLE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return common_response