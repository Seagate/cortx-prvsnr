#!/usr/bin/env python
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
import ..utils.pacemaker as pacemaker 
from .. .messages.user_messages import *

logger = logging.getLogger(__name__)

class CortxValidationsCall():

    def __init__(self):
        ''' Validations for cortx functionalities
        '''
        pass

    @staticmethod
    def consul_check():
        ''' Validations for Consul
        '''
        cmd = "ps -eaf | grep consul"
        res = run_subprocess_cmd(cmd)
        if res[0] == 0:
            response["message"]= str(CONSUL_SERVICE_CHECK)
        else:
            response["message"]= str(CONSUL_SERVICE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    @staticmethod
    def check_elasticsearch_service():
        ''' Validations for ES service
        '''
        cmd = "ps -eaf | grep elastic"
        res = run_subprocess_cmd(cmd)
        if res[0] == 0:
            response["message"]= str(ES_SERVICE_CHECK)
        else:
            response["message"]= str(ES_SERVICE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    @staticmethod
    def check_ioservice_service():
        ''' Validations for IO services
        '''
        cmd = "hctl status | grep unknown | grep -v m0_client"
        res = run_subprocess_cmd(cmd)
        if res[0] == 0:
            response["message"]= str(IO_SERVICE_CHECK)
        else:
            response["message"]= str(IO_SERVICE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response
