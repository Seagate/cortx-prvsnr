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
from provisioner import set_ntp


class NodePrepareTime(Command):
    """Cortx Setup API for configuring time"""
    _args = {
        'server': {
            'type': str,
            'default': 'time.seagate.com',
            'optional': True
        },
        'timezone': {
            'type': str,
            'default': 'UTC',
            'optional': True
        }
    }

    def run(self, **kwargs):
        """Time configuration command execution method.

        Execution:
        `cortx_setup node prepare time --server <ntp-server> --timezone <timezone>`
        """
        ntp_server = kwargs.get('server')
        ntp_timezone = kwargs.get('timezone')
        self.logger.info(f"Configuring Time")
        try:
            set_ntp(server=ntp_server, timezone=ntp_timezone)
            self.logger.info("Done")
        except Exception as e:
            print(e)
            self.logger.error("Time configuration failed")
