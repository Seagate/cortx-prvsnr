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

from ..command import Command


class NetworkConfig(Command):
    _args = {
        'mtu': {
            'type': int,
            'default': 1500,
            'optional': True
        },
        'public_ip': {
            'type': str,
            'default': '10.10.10.10',
            'optional': True
        },
        'network_interface': {
            'type': str,
            'default': ['eth0'],
            'nargs': '+',
            'optional': True}
    }

    def run(self, **kwargs):
        self.logger.info("My name is mazhe")
        print(f"this is for test {kwargs}")
