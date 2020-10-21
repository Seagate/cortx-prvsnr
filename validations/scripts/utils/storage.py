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
from .common import run_subprocess_cmd
from .. .messages.user_messages import *

logger = logging.getLogger(__name__)

class StorageValidations():

    def __init__(self):
        ''' Validations for pre-factory storage steps
        '''
        pass

    def volumes_accessible():
        ''' Validations for Enclosure Volumes
        '''
        cmd = "lsblk -S && ls -1 /dev/disk/by-id/scsi-*"
        common_response = run_subprocess_cmd(cmd, shell=True)
        return common_response

    def volumes_mapped():
        ''' Validations for Enclosure Volumes
        '''
        cmd_priority_50 = "multipath -ll | grep prio=50 | wc -l"
        cmd_priority_10 = "multipath -ll | grep prio=10 | wc -l"
        # TO DO: Create os function in common file
        common_response_50 = os.system(cmd_priority_50)
        print ("RESPONSE 50: " , common_response_50)
        common_response_10 = os.system(cmd_priority_10)
        return common_response_50, common_response_10