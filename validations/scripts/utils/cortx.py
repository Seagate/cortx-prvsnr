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

logger = logging.getLogger(__name__)

class CortxValidations():

    def __init__(self):
        ''' Validations for cortx functionalities
        '''
        pass

    def consul_service(self):
        ''' Validations for Consul
        '''
        cmd = "ps -eaf | grep consul"
        common_response = run_subprocess_cmd(cmd, shell=True)
        return common_response

    def elasticsearch_service(self):
        ''' Validations for ES service
        '''
        cmd = "ps -eaf | grep elastic"
        common_response = run_subprocess_cmd(cmd, shell=True)
        return common_response

    def ioservice_service(self):
        ''' Validations for IO services
        '''
        cmd = "hctl status | grep unknown | grep -v m0_client"
        common_response = run_subprocess_cmd(cmd, shell=True)
        return common_response
