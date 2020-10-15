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
from ..cluster import ClusterInfo
from ..common import setup_logging, run_subprocess_cmd, remote_execution, update_response
from ..network_checks import NetworkValidations

logger = logging.getLogger(__name__)

class BmcCheck:
    def __init__(self):
        """Get cluster information and store it"""
        self.private_data_ip_node_1="192.168.0.1"
        self.private_data_ip_node_2= "192.168.0.2"
        self.cls_info = ClusterInfo()


    @staticmethod
    def check_power_status(remote_ip=None):
        """This function check power status of chassis"""
        response = {}
        chassis_cmd = 'ipmitool chassis status'

        if remote_ip:
            response = remote_execution(remote_ip, chassis_cmd)
        else:
            response = run_subprocess_cmd(chassis_cmd)

        if response['ret_code']:
            response['message'] = "ERROR: Unable to check chassis status."
            return response
        else:
            response['message'] = "Received chassis status."

        msg = "BMC Power status not found"
        pw_status_chk = False
        output_lines = response['response'].split('\n')
        for line in output_lines:
            if "System Power" in line:
                pw_status = line.split(':')[-1].strip()
                msg = f"BMC System Power: {pw_status}"
                pw_status_chk = True if pw_status == 'on' else False
                break

        logger.info(msg)

        if not pw_status_chk:
            response['ret_code'] = 1
            response['message'] = f"{response['message']} {msg}"
        return response


    @staticmethod
    def get_bmc_ip():
        """This function returns BMC IP along with status of command"""
        cmd = "ipmitool lan print 1"
        response = run_subprocess_cmd(cmd)

        if response['ret_code']:
            response["message"] = "Failed to get BMC IP."
            return response

        output_lines = response['response'].split('\n')
        for line in output_lines:
            if "IP Address  " in line:
                response["message"] = line.split(':')[-1].strip()
                break

        return response


    @staticmethod
    def ping_bmc(bmc_ip, remote_host=None):
        """This function pings the given BMC ip and returns the status"""
        return NetworkValidations.check_ping(bmc_ip, remote_host)


    def is_bmc_accessible(self):
        """
        This function performs different operations to check whether BMC is
        accessible from both the nodes
        """
        response = {}

        # srvnode-1
        logger.info("Checking BMC connectivity from 'srvnode-1'")

        # Check power status
        logger.info("Checking Power status of chassis")
        resp = self.check_power_status()
        response = update_response(response, resp)
        if response['ret_code']:
            return response

        # Get BMC IP
        resp = self.get_bmc_ip()
        if resp['ret_code']:
            response = update_response(response, resp)
            return response
        bmc_ip = resp['message']

        # Ping BMC from srvnode-1
        resp = self.ping_bmc(bmc_ip)
        response = update_response(response, resp)
        if response['ret_code']:
            return response

        # srvnode-2
        logger.info("Checking BMC connectivity from 'srvnode-2'")

        # Get srvnode-2 private ip address
        pvt_ip_addr = self.cls_info.get_pvt_ip_addr('srvnode-2')
        if not pvt_ip_addr:
            pvt_ip_addr = self.private_data_ip_node_2

        # Check power status
        logger.info("Checking Power status of chassis")
        resp = self.check_power_status(pvt_ip_addr)
        response = update_response(response, resp)
        if response['ret_code']:
            return response

        # Ping BMC from srvnode-2
        resp = self.ping_bmc(bmc_ip, pvt_ip_addr)
        response = update_response(response, resp)

        return response



def main():
    setup_logging()

    bmc = BmcCheck()

    response = bmc.is_bmc_accessible()
    logger.info(response)


if __name__ == '__main__':
    main()
