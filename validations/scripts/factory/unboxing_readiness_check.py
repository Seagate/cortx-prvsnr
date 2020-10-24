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
from scripts.utils.cluster import ClusterValidations
from scripts.utils.pillar_get import PillarGet
from scripts.utils.bmc import BMCValidations
from scripts.utils.common import *
from scripts.utils.network_connectivity_checks import NetworkValidations
from messages.user_messages import *
logger = logging.getLogger(__name__)

class UnboxingValidationsCall():

    def __init__(self):
        ''' Validations for Pre-Unboxing
        '''
        self.cluster = ClusterValidations()
        self.bmc = BMCValidations()
        pass

#    def check_cluster_status(self):
#        ''' Validations for cluster status
#        '''
#        response = {}
#        nodes = PillarGet.get_pillar("cluster:node_list")
#        #get nodes
#        if not node_res['ret_code']:
#            nodes = node_res['response']
#            res = self.cluster.cluster_status()
#            for node in nodes:
#                if "{node}: Online":
#                    response["message"]= "{} in Cluster: Healthy".format(node)
#                else:
#                    response["message"]= str(CLUSTER_HEALTH_ERROR)
#                response["ret_code"]= res[0]
#                response["response"]= res[1]
#                response["error_msg"]= res[2]
#        else:
#            response["ret_code"]= node_res['ret_code']
#            response["response"]= node_res['response']
#            response["error_msg"]= node_res["error_msg"]
#            response["message"]= str(NODES_OFFLINE)
#        return response
#
#    def check_stonith_issues(self):
#        ''' Validations for STONITH issues
#        '''
#        response = {}
#        nodes = PillarGet.get_pillar("cluster:node_list")
#        res = self.cluster.stonith_issues()
#        #if (stop_response[0] and reboot_response[0] and err_response[0]) == 0:
#        if not res[0]:
#            response["message"]= str(STONITH_CHECK) 
#        else: 
#            response["message"]= str(STONITH_ERROR)
#        response["ret_code"]= res[0]
#        response["response"]= res[1]
#        response["error_msg"]= res[2]
#        return response


    def check_bmc_accessible(self):
        ''' Validations for BMC accessibility
        '''
        response = {}
        bmc_res = self.bmc.bmc_accessible()
        if not bmc_res["ret_code"]:
            response["message"]= str(BMC_ACCESSIBLE_CHECK)
        else:
            response["message"]= str(BMC_ACCESSIBLE_ERROR)
        response["ret_code"]= bmc_res["ret_code"]
        response["response"]= bmc_res["response"]
        response["error_msg"]= bmc_res["error_msg"]
        return response


    def check_controller_mc_accessible(self):
        ''' Validations for Controllers accessibility
        '''
        response = {}
        node_res = PillarGet.get_pillar("cluster:node_list")
        if not node_res['ret_code']:
            nodes = node_res['response']
            for node in nodes:
                ctrl_ip = PillarGet.get_pillar("cluster:{node}:bmc:ip")
                user = PillarGet.get_pillar("cluster:{node}:bmc:user")
                enc_secret = PillarGet.get_pillar("cluster:{node}:bmc:secret")
                get_decrypt_secret = decrypt_secret("ldap", enc_secret)
                if not get_decrypt_secret["ret_code"]:
                    passwd = get_decrypt_secret["response"]
                    ssh_ctrl_ip = ssh_remote_machine(hostname, user, passwd)
                    response["message"]= ssh_ctrl_ip["message"]
                else:
                    response["message"]= str(DECRYPT_PASSWD_FAILED)
        else:
            response["message"]= str(CTRL_IP_ACCESSIBLE_ERROR)

        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response
