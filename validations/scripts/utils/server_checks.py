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
from .network_connectivity_checks import NetworkValidations
from .pillar_get import PillarGet
from .common import run_subprocess_cmd


logger = logging.getLogger(__name__)


class ServerValidations():

    def verify_nodes_connectivity(self):
        """Validations for nodes."""
        logger.info("verify_nodes_connectivity check")
        res = PillarGet.get_pillar("cluster:node_list")
        if res['ret_code']:
            return res
        for node in res['response']:
            result = NetworkValidations.check_ping(node)
            if result['ret_code']:
                return result
        result['message'] = "Nodes are online"
        logger.debug(f"verify_nodes_online: resulted in {result}")
        return result

    def verif_node_communication(self):
        """validation salt  test.ping."""
        logger.info("verif_node_communication check")
        res = PillarGet.get_pillar("cluster:node_list")
        response = {}
        if res['ret_code']:
            return res
        for node in res['response']:
            result = run_subprocess_cmd(
                f"salt {node} test.ping --out=json", timeout=10
            )
            response['ret_code'] = result[0]
            response['response'] = result[1]
            response['error_msg'] = result[2]
            if response['ret_code']:
                response['message'] = f"Failed to communicate to {node}"
                return response
        response['message'] = f"Nodes communication is working"
        logger.debug(f"verif_node_communication: resulted in {response}")
        return response

    def verify_passwordless(self):
        """Validations for nodes."""
        logger.info("verify_passwordless check")
        res = PillarGet.get_hostnames()
        response = {}
        if res['ret_code']:
            return res
        for node in res['response']:
            result = run_subprocess_cmd(f"ssh {node} exit")
            response['ret_code'] = result[0]
            response['response'] = result[1]
            response['error_msg'] = result[2]
            if result[0]:
                response['message'] = f"No Passwordless ssh: {node}"
                return response
        response['message'] = "Verified Passwordless ssh"
        logger.debug(f"verify_passwordless: resulted in {response}")
        return response
