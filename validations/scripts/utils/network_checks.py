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

from .pillar_get import PillarGet  # noqa: E402
from .network_connectivity_checks import NetworkValidations

logger = logging.getLogger(__name__)


class NetworkChecks():

    @staticmethod
    def verify_mgmt_vip():
        '''Validations for mgmt_vip'''
        res = PillarGet.get_pillar("cluster:mgmt_vip")
        if res['ret_code']:
            res['message'] = "MGMT VIP is not set in pillars"
        else:
            res = NetworkValidations.check_ping(res['response'])
            if res['ret_code']:
                res['message'] = "Ping to MGMT VIP failed"
            else:
                res['message'] = "MGMT VIP is configured"
        return res

    @staticmethod
    def verify_cluster_ip():
        '''Validations for cluster_ip'''
        res = PillarGet.get_pillar("cluster:cluster_ip")
        if res['ret_code']:
            res['message'] = "Cluster IP is not set in pillars"
        else:
            res = NetworkValidations.check_ping(res['response'])
            if res['ret_code']:
                res['message'] = "Ping to Cluster IP failed"
            else:
                res['message'] = "Cluster IP is configured"
        return res

    @staticmethod
    def verify_public_data_ip():
        '''Validations for public data ip'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = PillarGet.get_pillar(f"cluster:{node}:network:data_nw:public_ip_addr")
            if result['ret_code']:
                result['message'] = f"Public data IP for {node} is not set in pillars"
                return result 
            result = NetworkValidations.check_ping(result['response'])
            if result['ret_code']:
                return result
        result['message'] = "Public data IP is configured"
        return result

    @staticmethod
    def verify_private_data_ip():
        '''Validations for private data ip'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = PillarGet.get_pillar(f"cluster:{node}:network:data_nw:pvt_ip_addr")
            if result['ret_code']:
                result['message'] = f"Private data IP for {node} is not set in pillars"
                return result
            result = NetworkValidations.check_ping(result['response'])
            if result['ret_code']:
                return result
        result['message'] = "Private data IP is configured"
        return result
