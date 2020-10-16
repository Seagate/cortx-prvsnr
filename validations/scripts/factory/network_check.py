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
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/utils")

from pillar_get import PillarGet  # noqa: E402


logger = logging.getLogger(__name__)


class NetworkChecks():

    def __init__(self):
        ''' Network validations
        '''
        pass

    @staticmethod
    def verify_mgmt_vip():
        ''' Validations for mgmt_vip
        '''
        res = PillarGet.get_pillar("cluster:mgmt_vip")
        if res['ret_code']:
            res['message'] = "MGMT VIP is not set in pillars"
        else:
            res['message'] = "MGMT VIP is set in pillars"
        return res

    @staticmethod
    def verify_cluster_ip():
        ''' Validations for cluster_ip
        '''
        res = PillarGet.get_pillar("cluster:cluster_ip")
        if res['ret_code']:
            res['message'] = "Cluster IP is not set in pillars"
        else:
            res['message'] = "Cluster IP is set in pillars"
        return res

    @staticmethod
    def verify_public_data_ip():
        ''' Validations for public data ip'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = PillarGet.get_pillar(f"cluster:{node}:network:data_nw:public_ip_addr")
            if result['ret_code']:
                result['message'] = f"Public data IP for {node} is not set in pillars"
            else:
                result['message'] = f"Public data IP for {node} is set in pillars"
            if not response.get("response", None):
                response = result
            else:
                if result['ret_code']:
                    response['ret_code'] = result['ret_code']
                response['response'] = [response['response'], result['response']]
                response['message'] = [response['message'], result['message']]
        return response

    @staticmethod
    def verify_private_data_ip():
        ''' Validations for private data ip'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = PillarGet.get_pillar(f"cluster:{node}:network:data_nw:pvt_ip_addr")
            if result['ret_code']:
                result['message'] = f"Private data IP for {node} is not set in pillars"
            else:
                result['message'] = f"Private data IP for {node} is set in pillars"
            if not response.get("response", None):
                response = result
            else:
                if result['ret_code']:
                    response['ret_code'] = result['ret_code']
                response['response'] = [response['response'], result['response']]
                response['message'] = [response['message'], result['message']]
        return response
