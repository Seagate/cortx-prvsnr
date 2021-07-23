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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

# CORTX package
from cortx.utils.conf_store import Conf
from ..command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE


class SetConfiguration(Command):
    _args = {
        'key': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Configuration key to set'
        },
        'value': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Configuration value to set'
        }
    }

    def run(self, key=None, value=None):
        """
        To set the configuration value in confstore
        :param key: key for which value to be set
        :param value: value to set for the respective key
        :return: None
        :Execution:
            'cortx_setup config set --key <key>  --value <value>'
        """
        if not key or not value:
            raise ValueError(
                "Invalid input. Expected Config param format: --key 'key' --value 'value'"
            )
        if value.strip():
            raise ValueError(
                "Invalid input. Value should not be en empty string"
            )
        self.load_conf_store(
            'node_info_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )
        self.logger.debug(f"Updating confstore key {key} with value {value}")

        value = int(value) if value.isdigit() else value
        Conf.set(
            'node_info_index',
            key,
            value
        )

        Conf.save('node_info_index')
