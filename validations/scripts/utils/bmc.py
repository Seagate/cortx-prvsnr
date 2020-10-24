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
        bmc_ip = []
        node_res = PillarGet.get_pillar("cluster:node_list")
        if node_res['ret_code']:
            return node_res
        nodes = node_res['response']
        for node in nodes:
            bmc_ip_get = PillarGet.get_pillar(f"cluster:{node}:bmc:ip")
            bmc_ip.append(bmc_ip_get["response"])

        common_response["response"] = bmc_ip 
        common_response["ret_code"]= node_res["ret_code"]
        common_response["error_msg"]= node_res["error_msg"]
        return common_response

    def ping_bmc(self):
        ''' Ping BMC IP
        '''
        response = {}
        res_ip_get = self.get_bmc_ip()
        res_ip = res_ip_get["response"]
        if res_ip_get['ret_code']:
            return res_ip_get
        for ip in res_ip:
            ping_check = NetworkValidations.check_ping(ip)
            if ping_check['ret_code']:
                ping_check["message"]= str(BMC_ACCESSIBLE_ERROR)
                return ping_check

        response["ret_code"]= ping_check['ret_code']
        response["message"]= str(BMC_ACCESSIBLE_CHECK)
        response["response"]= ping_check["response"]
        response["error_msg"]= ping_check["error_msg"]
        return response

    def bmc_accessible(self):
        ''' Validations for BMC accessibility
        '''
        response = {}
        cmd = "ipmitool chassis status | grep 'System Power'"
        common_response = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        bmc_ping_res = self.ping_bmc()
        if (("on" in str(common_response)) and (bmc_ping_res['ret_code'] == 0)):
            response["message"]= str(BMC_ACCESSIBLE_CHECK)
        else:
           response["message"]= str(BMC_ACCESSIBLE_ERROR)
        
        response["ret_code"]= bmc_ping_res["ret_code"]
        response["response"]= [str(common_response), bmc_ping_res["response"]]
        response["error_msg"]= bmc_ping_res["error_msg"]
        return response
