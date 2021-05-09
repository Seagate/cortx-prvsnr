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

##########################################################
# This code has been deprecated in favor of Nothbound API
##########################################################

# flake8: noqa
import json
import sys

import salt.client

from utils.pillar import _Pillar


# TODO DEPRECATED
class _NTP(object):

    #local client instance to send commands to minion
    def __init__(self, cfg_path: str=None):
        self.__local_client = salt.client.LocalClient()


    def update_pillar(self, time_dict: dict):
        with _Pillar() as pillar:
            data = pillar.pillar_data

            data['system']['ntp']['time_server'] = time_dict['time_server']
            data['system']['ntp']['timezone'] = time_dict['timezone']

            # Update pillar
            pillar.pillar_data = data


    def refresh_ntpd(self):

        #prvsnr_client instance to send commands to minion
        prvsnr_client = salt.client.LocalClient()

        #Apply configuration modification salt state
        ret_val = prvsnr_client.cmd('*', 'state.apply', ['system.chrony.config'])
        for val in ret_val.values():
            for task in val.values():
                if task['result']==False:
                        raise Exception("ERROR: NTP configuration update failed, " + task['comment'])

        #Apply service restart salt state
        ret_val = prvsnr_client.cmd('*', 'state.apply', ['system.chrony.update'])
        for val in ret_val.values():
            for task in val.values():
                if task['result']==False:
                        raise Exception("ERROR: NTP restart failed, " + task['comment'])

        return True
        

    def execute(self, time_dict: dict):
        # Stages
        # 1. Read incoming json
        # 2. Update pillar data
        # 3. Restart service using update

        time_dict = json.loads(time_dict)
        if 'time_server' not in time_dict or 'timezone' not in time_dict:
            raise Exception("ERROR: Insufficient input parameters.")

        # update pillar with new data
        self.update_pillar(time_dict)

        # Refresh NTPd service
        self.refresh_ntpd()



if __name__ == "__main__":

    time_data = """
                        {
                            "time_server": "time.seagate.com",
                            "timezone": "UTC"
                        }
                    """

    if len(sys.argv) >= 2:
        time_data = sys.argv[1]

    if not NTP().execute(time_data):
        sys.exit(2)
