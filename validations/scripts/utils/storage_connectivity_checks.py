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

from .pillar_get import PillarGet
from .common import run_subprocess_cmd


logger = logging.getLogger(__name__)


class StorageValidations():

    def verify_luns_consistency():
        '''Validations for LUNs are consistent across nodes'''
        res = PillarGet.get_hostnames()
        nodes = []
        response = {}
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res
        res = []
        for node in nodes:
            result = run_subprocess_cmd(f"ssh {node} lsblk -S| grep sas | wc -l")
            response['ret_code'] = result[0]
            response['response'] = result[1]
            response['error_msg'] = result[2]
            if result[0] or int(result[1]) == 0 or (int(result[1])%16) != 0:
                response['ret_code'] = 1
                response['message'] = ( 
                    "verify_luns_consistency:"
                    f"Inconsistent luns {int(result[1])} for {node}"
                )
                return response
            response['message'] = "Number of luns are same on nodes"
        return response

    def verify_multipath():
        '''Validations for multpath volumes'''
        res = run_subprocess_cmd("multipath -ll")
        response = {}
        if res[0]:
            response['ret_code'] = res[0]
            response['response'] = res[1]
            response['err_msg'] = res[2]
            response['message'] = "Failed to validate multipath"
            return response
        else:
            cmds = [
                   "multipath -ll | grep -B2 prio=50 | grep mpath | sort -k2.2 | wc -l",
                   "multipath -ll | grep -B2 prio=10 | grep mpath | sort -k2.2 | wc -l"
                ]
            result = {}
            for cmd in cmds:
                result = run_subprocess_cmd(f"multipath -ll | grep -B2 prio=50 | grep mpath | sort -k2.2 | wc -l")
                if result['ret_code'] or int(result['response']) != 8:
                    result['message'] = "Failed to verified multipaths on the device"
                    return result
            result['message'] = "Verified multipaths on the device"
        return result

