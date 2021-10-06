#!/bin/env python3

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
from cortx.provisioner.error import CortxProvisionerError
from cortx.provisioner.config_store import ConfigStore


class ConfigValidation:
    """ Validate Config """

    _cortx_conf_url = "yaml:///etc/cortx/cluster.conf"
    _solution_index = "solution_config"

    def __init__(self, solution_conf_url: str, cortx_conf_url: str = None):
        """ Validate conf_store config """

        self.solution_conf_url = solution_conf_url
        if cortx_conf_url is None:
            self.cortx_conf_url = self._cortx_conf_url
        self.cortx_conf_url = cortx_conf_url
        Conf.load(self._solution_index, self.solution_conf_url)
        self.cortx_config_store = ConfigStore(self.cortx_conf_url)

    def validate_config(self):
        """ Validate config_store """

        if Conf.get(ConfigValidation._solution_index, 'cluster') is not None:
            self.validate_storage_sets()
            self.validate_number_of_nodes()

        if Conf.get(ConfigValidation._solution_index, 'cortx') is not None:
            self.validate_external_services()

        return 0

    def validate_storage_sets(self):
        """ Check no of storage_sets present in conf_store
            and solution_config is same. """

        input_storage_sets = self.get_value_from_solution_config(
            'cluster>storage_sets')
        output_storage_sets = self.get_value_from_conf_store(
            'cluster>storage_set')

        if len(input_storage_sets) != len(output_storage_sets):
            raise CortxProvisionerError(errno.EINVAL,
                'No of storage_sets define in conf_store is not same as '
                f'solution_config. Storage_sets in {self.solution_conf_url} '
                f'is {len(input_storage_sets)} and in {self.cortx_conf_url} '
                f'is {len(output_storage_sets)}')

        return 0

    def validate_number_of_nodes(self):
        """ Check no. of nodes present in conf_store
            and solution config is same. """

        input_storage_sets = self.get_value_from_solution_config(
            'cluster>storage_sets')
        # Get nodes in each storage_set from solution_conf.
        storage_set_in_sol_conf = {}
        for storage_set in input_storage_sets:
            storage_set_name = storage_set['name']
            storage_set_in_sol_conf[storage_set_name] = storage_set['nodes']

        # Get nodes in each storage_set from Conf_store.
        storage_set_in_conf_store = {}
        nodes_in_conf_store = self.get_value_from_conf_store('node')
        for id_key in nodes_in_conf_store.keys():
            node_info = nodes_in_conf_store[id_key]
            storage_set_id = node_info['storage_set']
            if storage_set_in_conf_store.get(storage_set_id) is None:
                storage_set_in_conf_store[storage_set_id] = []
            storage_set_in_conf_store[storage_set_id].append(node_info)

        # validate nodes define for each storage_set in conf_store,
        # is same as nodes define in solution_config
        for key in storage_set_in_conf_store.keys():
            CS_nodes = storage_set_in_conf_store[key]
            SC_nodes = storage_set_in_sol_conf[key]
            if len(CS_nodes) != len(SC_nodes):
                raise CortxProvisionerError(errno.EINVAL,
                    'No of nodes define in conf_store is not same as solution_config.'
                    f' Nodes in {self.solution_conf_url} is {len(SC_nodes)} and '
                    f'in {self.cortx_conf_url} is {len(CS_nodes)}')

        return 0

    def validate_external_services(self):
        """" Validate no of external services in cortx config """

        sol_conf_ext_services = self.get_value_from_solution_config(
            'cortx>external')
        conf_stor_ext_services = self.get_value_from_conf_store(
            'cortx>external')

        if len(conf_stor_ext_services) != len(sol_conf_ext_services):
            raise CortxProvisionerError(errno.EINVAL,
                'External services define in conf_store is not same as '
                f'solution_config. External services in {self.solution_conf_url}'
                f' is {len(sol_conf_ext_services)} and in {self.cortx_conf_url}'
                f' is {len(conf_stor_ext_services)}')

        # Check endpoints
        for service in conf_stor_ext_services.keys():
            if (conf_stor_ext_services[service]['endpoints'] !=
                    sol_conf_ext_services[service]['endpoints']):
                raise CortxProvisionerError(errno.EINVAL,
                    f'{service} endpoints define in conf_store is not same as '
                    'solution_config.')


    def get_value_from_solution_config(self, key):
        """ Read config value for key from solution_config """

        config_value = Conf.get(
            ConfigValidation._solution_index, key)
        if config_value is None:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'{key} key is unspecified for {self.solution_conf_url}')

        return config_value

    def get_value_from_conf_store(self, key):
        """ Read config value from conf_store """

        config_value = self.cortx_config_store.get(key)
        if config_value is None:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'{key} key is unspecified for {self.cortx_conf_url}')

        return config_value
