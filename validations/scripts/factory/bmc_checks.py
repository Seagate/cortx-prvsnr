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

from ..utils.bmc import BMC as bmc
from ...messages.user_messages.error import (
    BMC_ACCESSIBLE_CHECK,
    BMC_ACCESSIBLE_ERROR
)
from ..utils.network_connectivity_checks import NetworkConnCheck
from ..utils.cluster import ClusterInfo

logger = logging.getLogger(__name__)

class BMCValidations():

    def __init__(self):
        ''' Validations for BMC steps
        '''
        self.bmc = bmc()
        self.nw_conn = NetworkConnCheck()

    def ping_bmc(self, remote_host=None):
        ''' Ping BMC IP
        '''
        logger.info("Ping BMC IP")

        response = self.bmc.get_bmc_ip()
        if not response['ret_code']:
            response = self.nw_conn.check_ping(response['message'], remote_host)

        return response


    def verify_bmc_power_status(self, remote_host=None):
        ''' Validations for BMC power status
        '''
        logger.info("verify_bmc_power_status check")

        response = self.bmc.get_bmc_power_status(remote_host)
        if not response['ret_code']:
            if response['message'] != 'on':
                response['ret_code'] = 1

        return response


    def verify_bmc_accessible(self):
        ''' Validations for BMC accessibility
        '''
        logger.info("verify_bmc_accessible check")

        response = {}
        cls = ClusterInfo()
        nodes = cls.get_nodes()
        for node in nodes:
            response = BMCValidations.verify_bmc_power_status(node)
            if response['ret_code']:
                return

            response = BMCValidations.ping_bmc(node)
            if response['ret_code']:
                return

        response['message'] = "BMC is accessible from both nodes"
        logger.debug(response)
        return response
