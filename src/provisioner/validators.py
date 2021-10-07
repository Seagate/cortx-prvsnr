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

import sys
import errno
import inspect

from cortx.utils.conf_store import Conf
from cortx.provisioner.error import CortxProvisionerError
from cortx.provisioner.config_store import ConfigStore


class Validator:
    """ Validator Framework """

    name = "validator"

    @staticmethod
    def process(*args):
        """ This interface needs to be implemented in derived class """
        pass

    @staticmethod
    def validate(validations: list, *args):
        """ Return the validator after parsing the validator list """

        validators = [
            y for x, y in inspect.getmembers(sys.modules[__name__])
            if x.endswith('Validator') and (
                y.name in validations or validations == ['all'])]
        for validator in validators:
            validator.process(*args)


class ConfigValidator(Validator):
    """ Config Validator """

    name = "config"
    _solution_index = "solution_config"
    _key_storage_set_sc = 'cluster>storage_sets'
    _key_storage_set_cs = 'cluster>storage_set'
    _key_ext_service = 'cortx>external'

    @staticmethod
    def process(*args):
        """ Process input parameters """

        if len(args) < 2:
            raise CortxProvisionerError(errno.EINVAL,
                'Please provide solution_config and conf_store '
                'url as input parameters.')
        elif len(args) >= 2:
            solution_conf_url = args[0]
            cortx_conf_url = args[1]

        ConfigValidator.load_config(solution_conf_url, cortx_conf_url)

        if Conf.get(ConfigValidator._solution_index, 'cluster') is not None:
            ConfigValidator()._check_storage_sets()
            ConfigValidator()._check_number_of_nodes()

        if Conf.get(ConfigValidator._solution_index, 'cortx') is not None:
            ConfigValidator()._check_external_services()

        # if cluster/cortx both keys are not present in file means file is
        # empty or file doesn't have required config.
        if (Conf.get(ConfigValidator._solution_index, 'cluster') is None and
            Conf.get(ConfigValidator._solution_index, 'cortx') is None):
            raise CortxProvisionerError(errno.EINVAL,
                'File is empty OR Cluster config and cortx config is not present in file.')

    @classmethod
    def load_config(cls, solution_conf_url, cortx_conf_url):
        """ Load config """

        cls.solution_conf_url = solution_conf_url
        cls.cortx_conf_url = cortx_conf_url
        Conf.load(cls._solution_index, cls.solution_conf_url)
        cls.cortx_config_store = ConfigStore(cls.cortx_conf_url)

    def _check_storage_sets(self):
        """ Check no of storage_sets present in conf_store
            and solution_config is same. """

        input_storage_sets = self._get_value_from_solution_config(
            ConfigValidator._key_storage_set_sc)
        output_storage_sets = self._get_value_from_conf_store(
            ConfigValidator._key_storage_set_cs)

        if len(input_storage_sets) != len(output_storage_sets):
            raise CortxProvisionerError(errno.EINVAL,
                'No of storage_sets define in conf_store is not same as '
                f'solution_config. Storage_sets in {self.solution_conf_url} '
                f'is {len(input_storage_sets)} and in {self.cortx_conf_url} '
                f'is {len(output_storage_sets)}')

        return 0

    def _check_number_of_nodes(self):
        """ Check no. of nodes present in conf_store
            and solution config is same. """

        input_storage_sets = self._get_value_from_solution_config(
            ConfigValidator._key_storage_set_sc)
        # Get nodes in each storage_set from solution_conf.
        storage_set_in_sol_conf = {}
        for storage_set in input_storage_sets:
            storage_set_name = storage_set['name']
            storage_set_in_sol_conf[storage_set_name] = storage_set['nodes']

        # Get nodes in each storage_set from Conf_store.
        storage_set_in_conf_store = {}
        nodes_in_conf_store = self._get_value_from_conf_store('node')
        for id_key in nodes_in_conf_store.keys():
            node_info = nodes_in_conf_store[id_key]
            storage_set_id = node_info['storage_set']
            if storage_set_in_conf_store.get(storage_set_id) is None:
                storage_set_in_conf_store[storage_set_id] = []
            storage_set_in_conf_store[storage_set_id].append(node_info)

        # validate nodes define for each storage_set in conf_store,
        # is same as nodes define in solution_config
        for key in storage_set_in_conf_store.keys():
            cs_nodes = storage_set_in_conf_store[key]
            sc_nodes = storage_set_in_sol_conf[key]
            if len(cs_nodes) != len(sc_nodes):
                raise CortxProvisionerError(errno.EINVAL,
                    'No of nodes define in conf_store is not same as solution_config.'
                    f' Nodes in {self.solution_conf_url} is {len(sc_nodes)} and '
                    f'in {self.cortx_conf_url} is {len(cs_nodes)}')

        return 0

    def _check_external_services(self):
        """" Validate no of external services in cortx config """

        sol_conf_ext_services = self._get_value_from_solution_config(
            ConfigValidator._key_ext_service)
        conf_stor_ext_services = self._get_value_from_conf_store(
            ConfigValidator._key_ext_service)

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
        return 0

    def _get_value_from_solution_config(self, key):
        """ Read config value for key from solution_config """

        config_value = Conf.get(
            ConfigValidator._solution_index, key)
        if config_value is None:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'{key} key is unspecified for {self.solution_conf_url}')

        return config_value

    def _get_value_from_conf_store(self, key):
        """ Read config value from conf_store """

        config_value = self.cortx_config_store.get(key)
        if config_value is None:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'{key} key is unspecified for {self.cortx_conf_url}')

        return config_value
