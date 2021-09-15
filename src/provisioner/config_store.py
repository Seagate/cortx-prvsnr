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

from cortx.utils.conf_store import Conf

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
        """

        for key, val in kvs:
            Conf.set(self._conf_idx, key, val)
        Conf.save(self._conf_idx)

    def set(self, key: str, val: str):
        """  """
        Conf.set(self._conf_idx, key, val)
        Conf.save(self._conf_idx)

    def get(self, key: str) -> str:
        """ Returns value for the given key """

        return Conf.get(self._conf_idx, key)
