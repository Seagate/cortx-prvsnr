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

import configparser
import logging
import subprocess
import time
import yaml
import os
import os.path
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/utils")

import config
import common
from common import run_subprocess_cmd

from pathlib import Path, PosixPath
from typing import (
    Tuple,
    Union,
    Optional,
    List
)

from errors import (
    ProvisionerError, SubprocessCmdError
)

logger = logging.getLogger(__name__)


class PacemakerValidations():

    def __init__(self):
        ''' Validations for Corosync Pacemaker
        '''
        pass

    def verify_corosync_status(self):
        ''' Validations for Pacemaker status
        '''
        cmd = "pcs status corosync"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            print( {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: Pacemaker Health Check OK" })
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: Pacemaker Health Check OK" }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: Pacemaker Health Check Not OK" }

    def verify_nodes_status(self):
        ''' Validations for nodes status
        '''
        cmd = "pcs status nodes"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: Nodes Health Check OK" }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: Nodes Health Check Not OK" }

    def get_resource_failcount(self):
        ''' Validations for resource fail count
        '''
        cmd = "pcs resource failcount show"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: " }
        # The Messages will be made common, 
        # so kept only the placeholder
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: " }

    def verify_cluster_status(self):
        ''' Validations for cluster status
        '''
        cmd = "pcs cluster status"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: " }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: " }


    def check_stonith_issues(self):
        ''' Validations for STONITH issues
        '''
        stop_cmd = "grep 'unable to stop resource' /var/log/pacemaker.log"
        stop_response = run_subprocess_cmd(cmd)
        reboot_cmd = "grep 'reboot' /var/log/corosync.log"
        reboot_response = run_subprocess_cmd(reboot_cmd)
        err_cmd = "grep 'error' /var/log/corosync.log"
        err_response = run_subprocess_cmd(err_cmd)
        # Need exact validation condition here - OR or AND ?
        if stop_response[0] or reboot_response[0] or err_response[0] == 0:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "CHECK: " }
        else:
            return {"ret_code": response[0],
                    "response": response[1],
                    "error_msg": response[2],
                    "message": "ERROR: " }
