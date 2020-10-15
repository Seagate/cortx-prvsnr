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
import yaml
from pathlib import Path
from ...messages.user_messages.error import (
    DEVICE_DOES_NOT_EXIST,
    FILE_READ_ERROR
)
from .cluster import ClusterInfo as Cls
from .common import run_subprocess_cmd, remote_execution
from .network_connectivity_check import NetworkConnCheck
logger = logging.getLogger(__name__)

class NetworkValidations():

    @staticmethod
    def get_ip_from_iface(iface, remote_host=None):
        """
        This function gets the IP from given interface. If remote host is
        mentioned, then it performs the operation on remote host.
        """

        response = {}
        pub_ip = None
        cmd = f"ip addr show dev {iface}"
        if remote_host:
            response = remote_execution(remote_host, cmd)
        else:
            response = run_subprocess_cmd(cmd)

        if response['ret_code']:
            response['message'] = str(DEVICE_DOES_NOT_EXIST).format(iface)
        else:
            resp_lines = response['response'].split('\n')
            for line in resp_lines:
                if 'inet' in line:
                    pub_ip = line.strip().split()[1].split('/')[0]
                    response['message'] = pub_ip
                    break

        if response['ret_code']:
            logger.error(f"{cmd} : {response['message']}")
        else:
            logger.debug(f"{cmd} : {response['message']}")
        return response


    @staticmethod
    def verify_public_data_ip():
        """
        This function checks if public data ip is configured successfully or
        not. If remote host is mentioned, then it checks if public data ip of
        remote host.
        """

        logger.info("verify_public_data_ip check")
        response = {}

        cls = Cls()
        nodes = cls.get_nodes()
        for node in nodes:
            iface = cls.get_pub_data_iface(node)
            for ifc in iface:
                if 's0f0' in ifc:
                    # Get public data ip from interface
                    response = NetworkValidations.get_ip_from_iface(ifc, remote_host=node)
                    if response['ret_code']:
                        return response

                    # Ping public data ip
                    response = NetworkConnCheck.check_ping(response['message'])
                    if response['ret_code']:
                        return response

        response['message'] = "Public data IP is configured for both nodes"
        logger.debug(response)
        return response
