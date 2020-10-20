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

from ..pillar_get import PillarGet
from ..common import run_subprocess_cmd


logger = logging.getLogger(__name__)


class LVMChecks():

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
        res = []
        for node in nodes:
            result = run_subprocess_cmd(f"ssh {node} vgdisplay | grep srvnode | wc -l")
            response['ret_code'] = result[0]
            response['response'] = result[1]
            response['error_msg'] = result[2]
            if result[0] or int(result[1]) == 0:
                response['message'] = "verify_lvm: Failed to get volumes for {node}"
                return response
            else:
                res.append(result[1])
        if len(res) > 1:
            pre_res = len(nodes)
            flag = True
            for resp in res:
                if pre_res and pre_res != int(resp.strip()):
                    flag = False
            response['response'] = res
            if not flag:
                response['ret_code'] = 1
                response['message'] = "Failed to verify LVM "
            else:
                response['message'] = "Verified LVM on both nodes"
        return response
