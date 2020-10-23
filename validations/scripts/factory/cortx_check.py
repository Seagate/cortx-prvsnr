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
from scripts.utils.cortx import CortxValidations as cortx 
from messages.user_messages import *
logger = logging.getLogger(__name__)

class CortxValidationsCall():

    def __init__(self):
        ''' Validations for cortx functionalities
        '''
        pass

    def check_consul_service(self):
        ''' Validations for Consul service
        '''
        response = {}
        res = cortx.consul_service()
        if res[0] == 0:
            response["message"]= str(CONSUL_SERVICE_CHECK)
        else:
            response["message"]= str(CONSUL_SERVICE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_elasticsearch_service(self):
        ''' Validations for ES service
        '''
        response = {}
        res = cortx.elasticsearch_service()
        if res[0] == 0:
            response["message"]= str(ES_SERVICE_CHECK)
        else:
            response["message"]= str(ES_SERVICE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response

    def check_ioservice_service(self):
        ''' Validations for IO services
        '''
        response = {}
        res = cortx.ioservice_service()
        if res[0] == 0:
            response["message"]= str(IO_SERVICE_CHECK)
        else:
            response["message"]= str(IO_SERVICE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response
