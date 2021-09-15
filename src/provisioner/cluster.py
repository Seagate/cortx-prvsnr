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
        validates a give node to have required properties
        Raises exception if there is any entry missing
        """
        for k in node.keys():
            if node[k] is None:
                raise VError(errno.EINVAL, f'{k} key is missing in node dict.')

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
        try:
            for node in self._node_list:
                node_id = node.pop('id')
                node['storage_set_count'] = 1
                components = {}
                for component in node.pop('components'):
                    comp_name = component.get('name')
                    components.update({
                        comp_name:  component.get('services')
                        })
                node['components'] = components
                if node['type'] == 'storage_node':
                    cvg_list = node.pop("storage")
                    node['storage'] = {
                        'cvg_count': len(cvg_list),
                        'cvg': cvg_list
                    }

                key_prefix = f'node>{node_id}'
                kvs.extend(self._get_kvs(key_prefix, node))

            config_store.set_kvs(kvs)

        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while adding node information into confstore {e}')


class CortxStorageSet:
    """ Represents CORTX storage_set """

    def __init__(self, storage_set: list = []):
        self._storage_sets = storage_set

    def save(self, config_store):
        """ Converts storage_set confstore keys
        and add into conf_store.
        constore representation for storage_set key:
         storage_set:
            - durability:
                dix:
                    data: '1'
                    parity: '7'
                    spare: '0'
                sns:
                    data: '8'
                    parity: '7'
                    spare: '0'
                name: storage-set-1
                nodes: []
        """
        kvs = []
        node_ids = []
        try:
            for storage_set in self._storage_sets:
                # Fetch node_ids of all nodes.
                for node in storage_set["nodes"]:
                    node_ids.append(node["id"])
                storage_set["nodes"] = node_ids
                # Read sns and dix value from storage_set
                durability = storage_set["durability"]
                for k, v in durability.items():
                    res = v.split("+")
                    durability[k] = {
                        "data": res[0],
                        "parity": res[1],
                        "spare": res[2]
                    }
                key_prefix = "cluster>storage_set"
                kvs.extend(CortxCluster()._get_kvs(key_prefix, storage_set))

            config_store.set_kvs(kvs)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while adding storage_sets to confstore {e}')
