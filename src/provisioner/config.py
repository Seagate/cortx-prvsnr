# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import errno
from cortx.provisioner.error import CortxProvisionerError
from cortx.utils.validator.error import VError
from cortx.utils.conf_store import Conf
from cortx.provisioner.log import Log
from cortx.provisioner import const

class CortxConfig:
    """CORTX Configuration"""

    def __init__(self, cortx_solution_config = None, cortx_release = None):
        """Create CORTX config"""
        if cortx_solution_config is None:
            cortx_solution_config = []
        self._cortx_release = cortx_release
        self._cortx_solution_config = cortx_solution_config
        CortxConfig._validate(self._cortx_solution_config)

    @staticmethod
    def _validate(cortx_solution_config: dict):
        """
        Validates a given node to have required properties

        Raises exception if there is any entry missing
        """
        required_keys_for_cortx_conf = ['external', 'common']

        for k in required_keys_for_cortx_conf:
            if cortx_solution_config.get(k) is None:
                raise VError(
                    errno.EINVAL, f"'{k}' property is unspecified in cortx_config.")

    def save(self, cortx_conf, cortx_solution_config):
        """Save cortx-config into confstore"""

        try:
            cortx_solution_config_keys = filter(lambda x: x.startswith(const.ROOT), Conf.get_keys(cortx_solution_config))
            cortx_conf.copy(cortx_solution_config, cortx_solution_config_keys)

            # Check for release key.
            release_spec = self._cortx_solution_config.get('common').get('release')
            is_valid, release_info = self._cortx_release.validate(release_spec)
            if is_valid is False:
                for key in release_info.keys():
                    release_key_path = f'{const.ROOT}>common>release>{key}'
                    Log.warn(f'Release key {release_key_path} is missing or has '
                        'incorrect value.')
                    Log.info(f'Adding key "{release_key_path}" '
                        f'and value "{release_info[key]}" in confstore.')
                    cortx_conf.set(release_key_path, release_info[key])

        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while adding CORTX config information into confstore {e}')
