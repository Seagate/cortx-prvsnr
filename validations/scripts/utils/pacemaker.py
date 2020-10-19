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
import subprocess
from common import run_subprocess_cmd
from pillar_get import PillarGet
from .. .messages.user_messages import *

logger = logging.getLogger(__name__)

class PacemakerValidations():

    def __init__(self):
        ''' Validations for Corosync Pacemaker
        '''
        pass

    @staticmethod
    def get_all_nodes():
        ''' Validations for Pacemaker status
        '''
        nodes = []
        node_res = PillarGet.get_pillar("cluster:node_list")
        return node_res

    @staticmethod
    def verify_corosync_status():
        ''' Validations for Pacemaker status
        '''
        cmd = "pcs status corosync"
        common_response = run_subprocess_cmd(cmd)
        return response

    @staticmethod
    def verify_nodes_status():
        ''' Validations for nodes status
        '''
        cmd = "pcs status nodes"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    @staticmethod
    def get_resource_failcount():
        ''' Validations for resource fail count
        '''
        cmd = "pcs resource failcount show"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    @staticmethod
    def verify_cluster_status():
        ''' Validations for cluster status
        '''
        cmd = "pcs cluster status"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    @staticmethod
    def stonith_issues():
        ''' Validations for STONITH issues
        '''
        stop_cmd = "grep 'unable to stop resource' /var/log/pacemaker.log"
        stop_response = run_subprocess_cmd(stop_cmd, shell=True)
        reboot_cmd = "grep 'reboot' /var/log/corosync.log"
        reboot_response = run_subprocess_cmd(reboot_cmd, shell=True)
        err_cmd = "grep 'error' /var/log/corosync.log"
        err_response = run_subprocess_cmd(err_cmd, shell=True)
        return stop_response, reboot_response, err_response
