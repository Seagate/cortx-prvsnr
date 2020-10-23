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

from scripts.utils.pillar_get import PillarGet  # noqa: E402
from scripts.utils.network_connectivity_checks import NetworkValidations

logger = logging.getLogger(__name__)


class NetworkChecks():

    def verify_mgmt_vip(self):
        """Validations for mgmt_vip."""
        logger.info("verify_mgmt_vip check")

        res = PillarGet.get_pillar("cluster:mgmt_vip")
        if res['ret_code']:
            res['message'] = "MGMT VIP is not set in pillars"
        else:
            res = NetworkValidations.check_ping(res['response'])
            if res['ret_code']:
                res['message'] = "Ping to MGMT VIP failed"
            else:
                res['message'] = "MGMT VIP is configured"

        logger.debug(f"verify_mgmt_vip: resulted in {res}")
        return res

    def verify_cluster_ip(self):
        """Validations for cluster_ip."""
        logger.info("verify_cluster_ip check")

        res = PillarGet.get_pillar("cluster:cluster_ip")
        if res['ret_code']:
            res['message'] = "Cluster IP is not set in pillars"
        else:
            res = NetworkValidations.check_ping(res['response'])
            if res['ret_code']:
                res['message'] = "Ping to Cluster IP failed"
            else:
                res['message'] = "Cluster IP is configured"

        logger.debug(f"verify_cluster_ip: resulted in {res}")
        return res

    def verify_public_data_ip(self):
        """Validations for public data ip."""
        logger.info("verify_public_data_ip check")

        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res

        for node in nodes:
            result = PillarGet.get_pillar(
                f"cluster:{node}:network:data_nw:public_ip_addr")
            if result['ret_code']:
                result['message'] = (
                    f"Public data IP for {node} is not set in pillars")
                return result
            result = NetworkValidations.check_ping(result['response'])
            if result['ret_code']:
                return result

        result['message'] = "Public data IP is configured"
        logger.debug(f"verify_public_data_ip: resulted in {result}")
        return result

    def verify_private_data_ip(self):
        """Validations for private data ip."""
        logger.info("verify_private_data_ip check")

        res = PillarGet.get_pillar("cluster:node_list")
        nodes = []
        if not res['ret_code']:
            nodes = res['response']
        else:
            return res

        for node in nodes:
            result = PillarGet.get_pillar(
                f"cluster:{node}:network:data_nw:pvt_ip_addr")
            if result['ret_code']:
                result['message'] = (
                    f"Private data IP for {node} is not set in pillars")
                return result
            result = NetworkValidations.check_ping(result['response'])
            if result['ret_code']:
                return result

        result['message'] = "Private data IP is configured"
        logger.debug(f"verify_private_data_ip: resulted in {result}")
        return result
