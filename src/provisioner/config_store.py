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
from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError
from cortx.provisioner.error import CortxProvisionerError

class ConfigStore:
    """ CORTX Config Store """

    _conf_idx = "cortx_conf"

    def __init__(self, conf_url):
        """ Initialize with the CONF URL """
        self._conf_url = conf_url
        Conf.load(self._conf_idx, self._conf_url, skip_reload=True)

    def set_kvs(self, kvs: list):
        """
        Parameters:
        kvs - List of KV tuple, e.g. [('k1','v1'),('k2','v2')]
        Where, k1, k2 - is full key path till the leaf key.
        """

        for key, val in kvs:
            try:
                Conf.set(self._conf_idx, key, val)
            except (AssertionError, ConfError) as e:
                raise CortxProvisionerError(errno.EINVAL,
                    f'Error occurred while adding key {key} and value {val}'
                    f' in confstore. {e}')
        Conf.save(self._conf_idx)

    def set(self, key: str, val: str):
        """Save key-value in CORTX confstore."""
        try:
            Conf.set(self._conf_idx, key, val)
            Conf.save(self._conf_idx)
        except (AssertionError, ConfError) as e:
            raise CortxProvisionerError(errno.EINVAL,
                f'Error occurred while adding key {key} and value {val}'
                f' in confstore. {e}')

    def copy(self, src_index: str):
        """Copy src_index config into CORTX confstore file."""
        try:
            Conf.copy(src_index, self._conf_idx)
        except (AssertionError, ConfError) as e:
            raise CortxProvisionerError(errno.EINVAL,
                f'Error occurred while copying config into confstore. {e}')

    def search(self, parent_key, search_key, value):
        """Search for given key under parent key in CORTX confstore."""
        return Conf.search(self._conf_idx, parent_key, search_key, value)

    def get(self, key: str) -> str:
        """ Returns value for the given key """

        return Conf.get(self._conf_idx, key)

    def delete(self, key: str):
        """Delete key from CORTX confstore."""
        Conf.delete(self._conf_idx, key)
