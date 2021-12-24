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
from cortx.provisioner.log import Log


class CortxCluster:
    """ Represents CORTX Cluster """

    def __init__(self, node_list: list = [], cortx_release = None):
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
        self._cortx_release = cortx_release
        for node in node_list:
            self._validate(node)

    def _validate(self, node: dict):
        """
        validates a give node to have required properties
        Raises exception if there is any entry missing
        """

        node_name = node.get('name')
        if node_name is None:
            raise CortxProvisionerError(errno.EINVAL, 'Missing name for the node entry')

        Log.debug("Validating node '%s' properties" % node_name)

        required_keys_for_node = ['id', 'components', 'storage_set', 'hostname']
        for k in required_keys_for_node:
            if node.get(k) is None:
                raise CortxProvisionerError(
                    errno.EINVAL,
                    f"'{k}' property is unspecified for node {node_name}")

    def add_node(self, node: dict):
        self._validate(node)
        self._node_list.append(node)

    def _get_kvs(self, prefix, node):
        kvs = []
        if isinstance(node, dict):
            for attr, val in node.items():
                kvs.extend(self._get_kvs(f'{prefix}>{attr}', val))
        elif isinstance(node, list):
            for i, n in enumerate(node):
                kvs.extend(self._get_kvs(f'{prefix}[{i}]', n))
        elif isinstance(node, str) or isinstance(node, int):
            kvs.append((prefix, node))
        return kvs

    def _get_component_kv_list(self, component_list: list, node_id: str):
        """Return list of confstore key-values for components."""
        # Create confstore keys, from given component list(config from config.yaml).
        component_kv_list = []
        component_kv_list.append((f'node>{node_id}>num_components', len(component_list)))
        for index, component in enumerate(component_list):
            key_prefix = f'node>{node_id}>components[{index}]'
            component_name = component['name']
            release_version = self._cortx_release.get_version(component_name)
            component_kv_list.extend((
                (f'{key_prefix}>name', component_name),
                (f'{key_prefix}>version', release_version)))

            service_list = component.get('services')
            if service_list:
                for index, service in enumerate(service_list):
                    component_kv_list.append((f'{key_prefix}>services[{index}]', service))

        return component_kv_list

    def _get_storage_kv_list(self, storage_spec: dict, node_id: str):
        """"Return list of confstore key-values for storage."""
        # Create confstore keys,from storage_spec(config from config.yaml).
        storage_kv_list = []
        key_prefix = f'node>{node_id}>storage'
        storage_kv_list.append((f'{key_prefix}>cvg_count', len(storage_spec)))
        for index, group in enumerate(storage_spec):
            for key, val in group.items():
                if key == 'devices':
                    metadata_device = group[key]['metadata']
                    # Convert metadata value to list.
                    if isinstance(metadata_device, str):
                        group[key]['metadata'] = metadata_device.split(',')
                if not isinstance(val, str):
                    storage_kv_list.extend(self._get_kvs(f'{key_prefix}>cvg[{index}]>{key}', val))
                else:
                    storage_kv_list.append((f'{key_prefix}>cvg[{index}]>{key}', val))
        return storage_kv_list

    def save(self, cortx_conf):
        """ Saves cluster information onto the conf store """

        kvs = []
        try:
            for node in self._node_list:
                node_id = node.pop('id')
                key_prefix = f'node>{node_id}'
                # confstore keys
                kvs.extend((
                    (f'{key_prefix}>cluster_id', node['cluster_id']),
                    (f'{key_prefix}>name', node['name']),
                    (f'{key_prefix}>hostname', node['hostname']),
                    (f'{key_prefix}>type', node['type']),
                    (f'{key_prefix}>storage_set', node['storage_set'])
                    ))
                component_list = node['components']
                kvs.extend(self._get_component_kv_list(component_list, node_id))
                storage_spec = node.get('storage')
                if storage_spec:
                    kvs.extend(self._get_storage_kv_list(storage_spec, node_id))
            cortx_conf.set_kvs(kvs)
        except (KeyError, IndexError) as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while adding node information into the confstore {e}')


class CortxStorageSet:
    """ Represents CORTX storage_set """

    def __init__(self, storage_sets: list = []):
        self._storage_sets = storage_sets
        for s_set in self._storage_sets:
            self._validate(s_set)

    def _validate(self, s_set: dict):
        """
        validates a give storage_sets to have required properties
        Raises exception if there is any entry missing
        """
        s_set_name = s_set.get('name')
        if s_set_name is None:
            raise CortxProvisionerError(
                errno.EINVAL, 'Missing name for the storage_set entry')

        Log.debug("Validating storage set '%s' properties" % s_set_name)

        required_keys_for_storage_set = ['durability', 'nodes']
        for k in required_keys_for_storage_set:
            if s_set.get(k) is None:
                raise VError(
                    errno.EINVAL,
                    f"'{k}' property is unspecified for storage_set {s_set_name}.")

    def save(self, cortx_conf):
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
        """
        kvs = []
        try:
            for index, storage_set in enumerate(self._storage_sets):
                key_prefix = f'cluster>storage_set[{index}]'
                kvs.append((f'{key_prefix}>name', storage_set['name']))
                nodes = storage_set['nodes']
                for node_idx, node in enumerate(nodes):
                    # confstore keys
                    kvs.append((f'{key_prefix}>nodes[{node_idx}]', node['id']))

                # Read sns and dix value from storage_set
                durability = storage_set['durability']
                for k, v in durability.items():
                    res = v.split('+')
                    # confstore keys
                    durability_key_prefix = f'{key_prefix}>durability>{k}'
                    kvs.extend(((f'{durability_key_prefix}>data', res[0]),
                        (f'{durability_key_prefix}>parity', res[1]),
                        (f'{durability_key_prefix}>spare', res[2])))
            cortx_conf.set_kvs(kvs)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while adding storage_sets to confstore {e}')
