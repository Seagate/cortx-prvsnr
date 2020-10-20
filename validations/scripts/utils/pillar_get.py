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
import json
import logging

from .common import run_subprocess_cmd  # noqa: E402

logger = logging.getLogger(__name__)


class PillarGet():

    @staticmethod
    def get_pillar(key):
        """Get pillar data for key"""
        cmd = f"salt-call pillar.get {key} --out=json"
        response = list(run_subprocess_cmd(cmd))
        if response[0] == 127:
            message = "get_pillar: salt-call: command not found"
        elif response[0] == 0:
            res = json.loads(response[1])
            res = res['local']
            if not res:
                message = f"get_pillar: No pillar data for key: {key}"
                response[2] = f"No pillar data for key: {key}"
                response[0] = 1
            else:
                response[1] = res
                message = f"pillar data {res}"
        else:
            message = "get_pillar: Failed to get pillar data"
        return {"ret_code": response[0],
                "response": response[1],
                "error_msg": response[2],
                "message": message}
