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
from .common import run_subprocess_cmd
import .pillar_get import PillarGet
from .. .messages.user_messages import *

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

    def bmc_accessible(self):
        ''' Validations for BMC accessibility
        '''
        cmd = "ipmitool chassis status | grep 'System Power'"
        common_response = run_subprocess_cmd(cmd_present, shell=True)
        # TO DO: Check os function result
        #common_response = os.system(cmd)
        return common_response