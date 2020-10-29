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
import subprocess
from scripts.utils.common import run_subprocess_cmd, check_subprocess_output
from scripts.utils.pillar_get import PillarGet
from messages.user_messages import *
from scripts.utils.network_connectivity_checks import NetworkValidations

logger = logging.getLogger(__name__)

class BMCValidations():

    def __init__(self):
        """ Validations for BMC steps
        """
        pass


    def get_bmc_ip(self):
        """ Get BMC IP along with status of command
        """
        logger.debug("Get BMC IP along with status of command")
        response = {}

        cmd = "ipmitool lan print 1 | grep 'IP Address'"
        res = check_subprocess_output(cmd)

        if res[0]:
            response['response'] = res[1]
            response['message'] = str(BMC_GET_IP_ERROR)
        else:
            response['response'] = res[1].split()[-1]
            response['message'] = str(BMC_GET_IP_SUCCESS).format(response['response'])

        response['ret_code'] = res[0]
        response['error_msg'] = res[2]

        logger.debug(response)
        return response


    def ping_bmc(self):
        """ Ping BMC IP
        """
        logger.debug("Ping BMC IP")

        response = self.get_bmc_ip()
        if response['ret_code']:
            return response

        response = NetworkValidations.check_ping(response['response'])
        logger.debug(response)
        return response


    def get_bmc_power_status(self):
        """ Get BMC power status
        """
        logger.debug("Get BMC power status")

        response = {}
        cmd = "ipmitool chassis status | grep 'System Power'"
        res = check_subprocess_output(cmd)

        if res[0]:
            response['response'] = res[1]
            response['message'] = str(BMC_POWER_STATUS_ERROR)
        else:
            response['response'] = res[1].split()[-1]
            response['message'] = str(BMC_POWER_STATUS_SUCCESS).format(response['response'])

        response['ret_code'] = res[0]
        response['error_msg'] = res[2]

        logger.debug(response)
        return response


    def bmc_stonith_config(self, bmc_ip, bmc_user, bmc_passwd):
        """ Validations for BMC STONITH accessibility
        """
        response = {}
        cmd = f"fence_ipmilan -P -a {bmc_ip} -o status -l {bmc_user} -p {bmc_passwd}"
        common_response = run_subprocess_cmd(cmd)
        if not common_response[0]:
            response["message"]= str(BMC_STONITH_CHECK)
        else:
            response["message"]= str(BMC_STONITH_ERROR)

        response["ret_code"]= common_response[0]
        response["response"]= common_response[1]
        response["error_msg"]= common_response[2]
        return response
