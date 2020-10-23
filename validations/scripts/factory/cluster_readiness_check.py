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
from scripts.utils.network_connectivity_checks import NetworkValidations
from messages.user_messages import *
logger = logging.getLogger(__name__)

class ClusterValidationsCall():

    def __init__(self):
        ''' Validations for Corosync Pacemaker
        '''
        self.cluster = ClusterValidations()
        self.bmc = BMCValidations()
        pass

    def check_corosync_status(self):
        ''' Validations for Pacemaker status
        '''
        response = {}
        node_res = PillarGet.get_pillar("cluster:node_list")
        #get nodes
        #if not node_res['ret_code']:
        nodes = node_res['response']
        res = self.cluster.corosync_status()
        for node in nodes:
            if node in res[1]: 
                response["message"]= str(PACEMAKER_HEALTH_CHECK)
            else:
                response["message"]= str(PACEMAKER_HEALTH_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_nodes_status(self):
        ''' Validations for nodes status
        '''
        response = {}
        nodes = PillarGet.get_pillar("cluster:node_list")
        #get nodes
        if not node_res['ret_code']:
            nodes = node_res['response']
        res = cluster.nodes_status()
        for node in nodes:
            if "Online" and node in res[1]:
                response["message"]= str(NODES_ONLINE)
            else:
                response["message"]= str(NODES_OFFLINE)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_get_resource_failcount(self):
        ''' Validations for resource fail count
        '''
        response = {}
        nodes = PillarGet.get_pillar("cluster:node_list")
        #get nodes
        if not node_res['ret_code']:
            nodes = node_res['response']
            res = cluster.get_resource_failcount()
            if res[1] == " ":
                response["message"]= str(RESOURCE_FAIL_CHECK)
            else:
                response["message"]= str(RESOURCE_FAIL_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_cluster_status(self):
        ''' Validations for cluster status
        '''
        response = {}
        nodes = PillarGet.get_pillar("cluster:node_list")
        #get nodes
        if not node_res['ret_code']:
            nodes = node_res['response']
        res = cluster.cluster_status()
        for node in nodes:
            if "{node}: Online": 
                response["message"]= "{} in Cluster: Healthy".format(node)
            else:
                response["message"]= str(CLUSTER_HEALTH_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_stonith_issues(self):
        ''' Validations for STONITH issues
        '''
        response = {}
        nodes = PillarGet.get_pillar("cluster:node_list")
        #get nodes
        #if not node_res['ret_code']:
        #    nodes = node_res['response']
        #for node in nodes: 
        res = cluster.stonith_issues()
        #if (stop_response[0] and reboot_response[0] and err_response[0]) == 0: 
        if not res[0]:
            response["message"]= str(STONITH_CHECK) 
        else: 
            response["message"]= str(STONITH_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def ping_bmc(self):
        ''' Ping BMC IP
        '''
        response = {}
        res_ip = self.bmc.get_bmc_ip()
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

    def check_bmc_accessible(self):
        ''' Validations for BMC accessibility
        '''
        response = {}
        bmc_res = self.bmc.bmc_accessible()
        bmc_ping_res = self.bmc.ping_bmc() 
        if bmc_res[0] and bmc_ping_res[0] == 0:
            response["message"]= str(BMC_ACCESSIBLE_CHECK)
        else:
            response["message"]= str(BMC_ACCESSIBLE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response
