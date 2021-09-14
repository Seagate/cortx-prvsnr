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

from cortx.provisioner.config_store import ConfigStore
from cortx.provisioner.error import CortxProvisionerError


class CortxCluster:
    """ Represents CORTX Cluster """

    def __init__(self, node_list: list = []):
        """
        Creates cluster from the list of nodes.
        Each node in the is is a dict and contains following attributes
        - name: <name>
          id: <uniq id>
          storage_set: <storage_set_name>
          hostname: <fqdn>
          components:
          - name: <component 1>
            services:
            - <service name 1>
            - <service name 2>
          - name: <component 2>
            ...
          storage:
          - name: <cvg name>
            type: <cvg type>
            data_devices:
            - /dev/<device 1>
            - /dev/<device 2>
            metadata_devices:
            - /dev/<device 1>
            - /dev/<device 2>
        """
        self._node_list = node_list
        for node in node_list:
            self._validate(node)

    def _validate(self, node: dict):
        """ 
        validates a give node to habve required properties
        Raises exception if there is any entry missing
        """
        pass

    def add_node(self, node: dict):
        self._validate(node)
        self._node_list.append(node)

    def _get_kvs(self, prefix, node):
        kvs = []
        if type(node) == dict:
            for attr, val in node.items():
                kvs.extend(self._get_kvs(f'{prefix}>{attr}', val))
        elif type(node) == list:
            for i in range(0, len(node)):
                kvs.extend(self._get_kvs(f'{prefix}[{i}]', node[i]))
        elif type(node) == str:
            kvs.append((prefix, node))
        return kvs

    def save(self, config_store):
        """ Saves cluster information onto the conf store """

        kvs = []
        for node in self._node_list:
            node_id = node['id']
            key_prefix = f'node>{node_id}'
            kvs.extend(self._get_kvs(key_prefix, node))

        config_store.set_kvs(kvs)
