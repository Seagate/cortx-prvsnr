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
import ..utils.storage as storage
from .. .messages.user_messages import *
logger = logging.getLogger(__name__)

class HardwareValidationsCall():

    def __init__(self):
        ''' Validations for pre-factory storage steps
        '''
        pass

    def check_volumes_accessible():
        ''' Validations for Enclosure Volumes
        '''
        response = {}
        res = storage.volumes_accessible()
        if not res[0]:
            response["message"]= str(VOLUMES_ACCESSIBLE_CHECK)
        else:
            response["message"]= str(VOLUMES_ACCESSIBLE_ERROR)
        response["ret_code"]= res[0]
        response["response"]= res[1]
        response["error_msg"]= res[2]
        return response


    def check_volumes_mapped():
        ''' Validations for Enclosure Volumes
        '''
        response = {}
        res = storage.volumes_mapped()
        if res == "16":
            response["message"]= str(VOLUMES_MAPPED_TO_CNTRLRS_CHECK)
        else:
            response["message"]= str(VOLUMES_MAPPED_TO_CNTRLRS_ERROR)
        response["ret_code"]= "0"
        response["response"]= int(res)
        response["error_msg"]= "NULL"
        return response