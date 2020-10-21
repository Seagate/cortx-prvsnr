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
from .common import run_subprocess_cmd
from .pillar_get import PillarGet
from .. .messages.user_messages import *

logger = logging.getLogger(__name__)

class ClusterValidations():

    def __init__(self):
        ''' Validations for Corosync Pacemaker
        '''
        pass

    def corosync_status(self):
        ''' Validations for Pacemaker status
        '''
        cmd = "pcs status corosync"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    def nodes_status(self):
        ''' Validations for nodes status
        '''
        cmd = "pcs status nodes"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    def get_resource_failcount(self):
        ''' Validations for resource fail count
        '''
        cmd = "pcs resource failcount show"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    def cluster_status(self):
        ''' Validations for cluster status
        '''
        cmd = "pcs cluster status"
        common_response = run_subprocess_cmd(cmd)
        return common_response

    def stonith_issues(self):
        ''' Validations for STONITH issues
        '''
        stop_cmd = "grep 'unable to stop resource' /var/log/pacemaker.log"
        stop_response = run_subprocess_cmd(stop_cmd, shell=True)
        reboot_cmd = "grep 'reboot' /var/log/corosync.log"
        reboot_response = run_subprocess_cmd(reboot_cmd, shell=True)
        err_cmd = "grep 'error' /var/log/corosync.log"
        err_response = run_subprocess_cmd(err_cmd, shell=True)
        return (stop_response, reboot_response, err_response)