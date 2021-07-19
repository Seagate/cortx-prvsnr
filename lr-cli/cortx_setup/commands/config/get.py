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

# Cortx Setup API for LR-Node Stamping Signature operations


from pathlib import Path
from ..command import Command

# CORTX package
from cortx.utils.conf_store import Conf
from cortx_setup.config import CONFSTORE_CLUSTER_FILE


class GetConfiguration(Command):
    _args = {
        'key': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Configuration details to retrieve for this key'
        }
    }

    def run(self, key=None):
        """
        To get the value of specific key
        :param key: key
        :return: Value read from confstore
        :Execution:
            'cortx_setup config get --key <key>'
        """
        if not key:
            raise ValueError(
               "Invalid input. Expected Config key to get the value in format: --key 'key'."
            )

        index = 'node_info_index'
        Conf.load(index, f'json://{CONFSTORE_CLUSTER_FILE}')
        try:
            val_fr_conf = Conf.get(index, key)
            self.logger.debug(f"Config value for '{key}' : {val_fr_conf}")
            return val_fr_conf
        except ValueError as exc:
            raise ValueError(
              "Failed to get config value from ConfStore: %s" % str(exc)
            )
