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
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/utils")

from network_checks import NetworkValidations  # noqa: E402
from pillar_get import PillarGet  # noqa: E402
from ..utils.common import run_subprocess_cmd  # noqa: E402


logger = logging.getLogger(__name__)


class ControllerValidations():

    def __init__(self):
        ''' Server validations
        '''
        pass

    @staticmethod
    def verify_access_to_controller():
        ''' Validations Access to controllers  '''
        controllers = ['primary_mc', 'secondary_mc']
        response = {}
        for controller in controllers:
            result = PillarGet.get_pillar(f"storage_enclosure:controller:{controller}:ip")
            if not result['ret_code']:
                result = NetworkValidations.check_ping(result['response'])
            if not response.get("response", None):
                response = result
            else:
                if result['ret_code']:
                    response['ret_code'] = result['ret_code']
                response['response'] = [response['response'], result['response']]
                response['message'] = [response['message'], result['message']]
        return response
