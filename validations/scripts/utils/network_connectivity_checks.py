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


class NetworkValidations():

    @staticmethod
    def check_ping(ip):
        """Check if IP's are reachable"""
        cmd = f"ping -c 1 {ip}"
        response = run_subprocess_cmd(cmd)
        if response[0] == 0:
            message = f"{ip} is reachable"
        elif response[0] == 1:
            message = f"check_ping: {ip}: Destination Host Unreachable"
        elif response[0] == 2:
            message = f"check_ping: {ip}: Name or service not known"
        else:
            message = f"check_ping: {ip}: Not reachable"
        return {"ret_code": response[0],
                "response": response[1],
                "error_msg": response[2],
                "message": message}
