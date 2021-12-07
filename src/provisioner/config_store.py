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
        for key, val in kvs.copy():
            try:
                Conf.set(self._conf_idx, key, val)
                kvs.remove((key, val))
            except AssertionError:
                # For consul(confstore backend),
                # value should be string type.
                key_value_list = self._parse_key_values(kvs)
                for key, val in key_value_list:
                    Conf.set(self._conf_idx, key, val)
        Conf.save(self._conf_idx)

    def set(self, key: str, val: str):
        """  """
        Conf.set(self._conf_idx, key, val)
        Conf.save(self._conf_idx)

    def get(self, key: str) -> str:
        """ Returns value for the given key """

        return Conf.get(self._conf_idx, key)

    def _get_kvs(self, prefix, conf_value):
        """Convert list,dict,int value into string type value.."""
        kvs = []
        if isinstance(conf_value, dict):
            for attr, val in conf_value.items():
                kvs.extend(self._get_kvs(f'{prefix}>{attr}', val))
        elif isinstance(conf_value, list):
            for i, list_attr in enumerate(conf_value):
                kvs.extend(self._get_kvs(f'{prefix}[{i}]', list_attr))
        elif isinstance(conf_value, int):
            kvs.append((prefix, str(conf_value)))
        elif isinstance(conf_value, str):
            kvs.append((prefix, conf_value))
        return kvs

    def _parse_key_values(self, kvs):
        """Return list containing key-values pair in string format."""
        parsed_key_value = []
        for key, val in kvs:
            parsed_key_value.extend(self._get_kvs(key, val))
        return parsed_key_value
