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
    DEST_HOST_NOT_REACHABLE,
    NAME_OR_SERVICE_NOT_KNOWN,
    NOT_REACHABLE
)

logger = logging.getLogger(__name__)

class NetworkConnCheck():

    def __init__(self):
        """ Initialize network connection
        """
        pass


    def check_ping(self, ip, remote_host=None):
        """ This function checks if IP is reachable. If remote host is mentioned,
            then it checks if ip is reachable from remote host.
        """

        cmd = f"ping -c 1 {ip}"
        if remote_host:
            response = remote_execution(remote_host, cmd)
        else:
            response = run_subprocess_cmd(cmd)

        if response['ret_code'] == 0:
            response['message'] = f"{ip} is reachable"
        elif response['ret_code'] == 1:
            response['message'] = f"{str(DEST_HOST_NOT_REACHABLE)} : {ip}"
        elif response['ret_code'] == 2:
            response['message'] = f"{str(NAME_OR_SERVICE_NOT_KNOWN)} : {ip}"
        else:
            response['message'] = f"{str(NOT_REACHABLE)} : {ip}"

        if response['ret_code']:
            logger.error(f"'{cmd}' : '{response['message']}'")
        else:
            logger.debug(f"'{cmd}' : '{response['message']}'")

        return response
