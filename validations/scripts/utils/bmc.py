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
from .common import run_subprocess_cmd, remote_execution
from ...messages.user_messages.error import (
    BMC_CHASSIS_ERROR,
    BMC_POWER_STATUS_ERROR,
    BMC_IP_ERROR
)
import .pillar_get import PillarGet

logger = logging.getLogger(__name__)

class BMC():

    def __init__(self):
        """ Get BMC Details
        """
        self.pillar = PillarGet()
        pass


    def get_bmc_ip(self, remote_host=None):
        """ Get BMC IP along with status of command
        """
        logger.info("Get BMC IP")

        cmd = "ipmitool lan print 1"
        if remote_host:
            response = remote_execution(remote_host, cmd)
        else:
            response = run_subprocess_cmd(cmd)

        if response['ret_code']:
            response["message"] = str(BMC_IP_ERROR)
        else:
            output_lines = response['response'].split('\n')
            for line in output_lines:
                if "IP Address  " in line:
                    response["message"] = line.split(':')[-1].strip()
                    break

        if response['ret_code']:
            logger.error(f"'{cmd}' : '{response['message']}'")
        else:
            logger.debug(f"'{cmd}' : '{response['message']}'")

        return response


    def get_bmc_power_status(self, remote_host=None):
        """ Get BMC Power Status
        """
        logger.info("Get BMC Power Status")

        response = {}
        cmd = "ipmitool chassis status | grep 'System Power'"
        if remote_host:
            response = remote_execution(remote_host, cmd)
        else:
            response = run_subprocess_cmd(cmd)

        if response['ret_code']:
            response['message'] = str(BMC_CHASSIS_ERROR)
        else:
            if "System Power" in response['response']:
                response['message'] = response['response'].split(':')[-1].strip()
            else:
                response['ret_code'] = 1
                response['message'] = str(BMC_POWER_STATUS_ERROR)

        if response['ret_code']:
            logger.error(f"'{cmd}' : '{response['message']}'")
        else:
            logger.debug(f"'{cmd}' : '{response['message']}'")

        return response

    def get_bmc_user(self, node):
        """ Get BMC User
        """
        logger.info("Get BMC User and Password")
        return self.pillar.get_pillar(f"cluster:{node}:bmc:user")

    def get_bmc_passwd(self, node):
        """ Get BMC Password
        """
        logger.info("Get BMC Password")
        return self.pillar.get_pillar(f"cluster:{node}:bmc:secret")
