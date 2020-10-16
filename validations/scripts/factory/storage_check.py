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
from ..utils.common import run_subprocess_cmd  # noqa: E402


logger = logging.getLogger(__name__)


class StorageValidations():

    @staticmethod
    def verify_luns_consistency():
        '''Validations for LUNs are consistent across nodes'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = run_subprocess_cmd(f"ssh {node} lsblk -S | wc -l")
            if not response.get("response", None):
                response['ret_code'] = result[0]
                response['response'] = result[1]
                response['error_msg'] = result[2]
            else:
                if result[0]:
                    response['ret_code'] = result[0]
                response['response'] = [response['response'], result[1]]
        if len(nodes) > 1:
            pre_res = 0
            flag = True
            for resp in response['response']:
                if pre_res and pre_res != resp:
                    flag = False
            if not flag:
                response['message'] = "Number of luns are not same on nodes"
            else:
                response['message'] = "Number of luns are same on nodes"
        return response

    @staticmethod
    def verify_lvm():
        '''Validations for LVM'''
        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        for node in nodes:
            result = run_subprocess_cmd(f"ssh {node} vgdisplay | grep srvnode | wc -l")
            if not response.get("response", None):
                response['ret_code'] = result[0]
                response['response'] = result[1]
                response['error_msg'] = result[2]
            else:
                if result[0]:
                    response['ret_code'] = result[0]
                response['response'] = [response['response'], result[1]]
                response['error_msg'] = result[2]
        if len(nodes) > 1:
            pre_res = len(nodes)
            flag = True
            for resp in response['response']:
                if pre_res and pre_res != int(resp.strip()):
                    flag = False
            if not flag:
                response['message'] = "Failed to verify LVM "
            else:
                response['message'] = "LVM  are present on nodes"
        return response
