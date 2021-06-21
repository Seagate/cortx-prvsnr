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

from cortx_setup.commands.command import Command
from provisioner.api import grains_get
from cortx_setup.validate import host
from cortx_setup.commands.common_utils import get_machine_id
from provisioner.commands import PillarSet
from provisioner.salt import (
    local_minion_id,
    StatesApplier
)


class NodePrepareTime(Command):
    """Cortx Setup API for configuring time"""
    _args = {
        'server': {
            'type': host,
            'default': 'time.seagate.com',
            'optional': True
        },
        'timezone': {
            'type': str,
            'default': 'UTC',
            'optional': True
        }
    }

    def set_server_time(self):
        """Sets time on the server"""
        StatesApplier.apply(
            [
                "components.system.chrony.config",
                "components.system.chrony.stop",
                "components.system.chrony.start"
            ]
        )

    def set_enclosure_time(self):
        """Sets time on the enclosure"""
        StatesApplier.apply(
            [ "components.controller.ntp" ]
        )

    def run(self, **kwargs):
        """Time configuration command execution method.

        Execution:
        `cortx_setup node prepare time --server <ntp-server> --timezone <timezone>`
        """

        node_id = local_minion_id()
        ntp_server = kwargs.get('server')
        ntp_timezone = kwargs.get('timezone')

        PillarSet().run(
            'system/ntp/time_server',
            ntp_server,
            local=True
        )

        PillarSet().run(
            'system/ntp/time_zone',
            ntp_timezone,
            local=True
        )

        try:
            self.logger.debug(f"Setting time on node with server={ntp_server} & timezone={ntp_timezone}")
            self.set_server_time()
            machine_id = get_machine_id(node_id)
            enclosure_id = grains_get("enclosure_id")[node_id]["enclosure_id"]
            if enclosure_id:
                if not machine_id in enclosure_id:   # check if the system is VM or HW
                    self.logger.debug(f"Setting time on enclosure with server={ntp_server} & timezone={ntp_timezone}")
                    self.set_enclosure_time()
        except Exception as e:
            self.logger.error(f"Time configuration failed\n {str(e)}")
            raise e
