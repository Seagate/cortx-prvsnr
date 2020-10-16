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

from network_checks import NetworkValidations  # noqa: E402
from pillar_get import PillarGet  # noqa: E402
from ..utils.common import run_subprocess_cmd  # noqa: E402


logger = logging.getLogger(__name__)


class ServerValidations():

    def __init__(self):
        ''' Server validations
        '''
        pass

    @staticmethod
    def verify_nodes_online():
        ''' Validations for nodes'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = NetworkValidations.check_ping(node)
            if not response.get("response", None):
                response = result
            else:
                if result['ret_code']:
                    response['ret_code'] = result['ret_code']
                response['response'] = [response['response'], result['response']]
                response['message'] = [response['message'], result['message']]
        return response

    @staticmethod
    def verif_node_communication():
        """ validation salt '*' test.ping"""
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = run_subprocess_cmd(f"salt {node} test.ping --out=json", timeout=10)
            if result[0]:
                message = f"Failed to communicate to {node}"
            else:
                message = f"Able to communicate to {node}"
            if not response.get("response", None):
                response['ret_code'] = result[0]
                response['response'] = result[1]
                response['error_msg'] = result[2]
                response['message'] = message
            else:
                if result[0]:
                    response['ret_code'] = result[0]
                response['response'] = [response['response'], result[1]]
                response['message'] = [response['message'], message]
        return response

    @staticmethod
    def verify_passwordless():
        ''' Validations for nodes'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        flag = True
        print(nodes)
        for node in nodes:
            result = run_subprocess_cmd(f"ssh {node} exit")
            if result[0]:
                flag = False
                if not response.get("response", None):
                    response['ret_code'] = result[0]
                    response['response'] = result[1]
                    response['error_msg'] = result[2]
                    response['message'] = f"No Passwordless ssh: {node}"
                else:
                    if result[0]:
                        response['ret_code'] = result[0]
                    response['response'] = [response['response'], result[1]]
                    response['message'] = [response['message'], f"No Passwordless ssh: {node}"]
        if flag:
            response['ret_code'] = result[0]
            response['response'] = ""
            response['error_msg'] = ""
            response['message'] = f"Verified Passwordless ssh"
        return response
