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
from cortx.provisioner.log import Log
from cortx.provisioner.config_store import ConfigStore
from cortx.utils.cortx import Const


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
            ConfigValidator()._validate_components()
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
        cls.cortx_conf = ConfigStore(cls.cortx_conf_url)

    def _check_storage_sets(self):
        """Validate storage_sets present in cortx_conf."""
        solution_config_storage_sets = self._get_config(
            ConfigValidator._key_storage_set_sc)

        storage_set_counter = 0
        while self.cortx_conf.get(
            f'cluster>storage_set[{storage_set_counter}]>name') is not None:
            storage_set_counter = storage_set_counter + 1
        if len(solution_config_storage_sets) != storage_set_counter:
            Log.debug(f'Number of storage_sets define in {self.solution_conf_url} is '
                f'{len(solution_config_storage_sets)} and in {self.cortx_conf_url} '
                f'is {storage_set_counter}')
            raise CortxProvisionerError(errno.EINVAL,
                f'Number of storage_sets define in {self.cortx_conf_url} '
                f'and {self.solution_conf_url} is not equal.')
        return 0

    def _check_number_of_nodes(self):
        """Validate number of nodes specified in cortx_conf."""
        solution_config_storage_sets = self._get_config(
            ConfigValidator._key_storage_set_sc)
        for storage_set in solution_config_storage_sets:
            storage_set_name = storage_set['name']
            solution_config_nodes = storage_set['nodes']
            # Get number of nodes from confstore which has same storage_set_name.
            conf_store_nodes = self.cortx_conf.search(
                'node', 'storage_set', storage_set_name)
            if len(solution_config_nodes) != len(conf_store_nodes):
                Log.debug(f'Number of nodes define in {self.solution_conf_url} is '
                    f'{len(solution_config_nodes)} and {self.cortx_conf_url} is '
                    f'{len(conf_store_nodes)}')
                raise CortxProvisionerError(errno.EINVAL,
                    f'Number of nodes define in {self.cortx_conf_url} and '
                    f'{self.solution_conf_url} is not equal.')
        return 0

    def _check_external_services(self):
        """Validate external services and its endpoints in cortx config."""
        # Get external services from config.yaml
        solution_config_services = self._get_config(ConfigValidator._key_ext_service)
        for service in solution_config_services.keys():
            key_prefix = f'{ConfigValidator._key_ext_service}>{service}'
            if self._get_value_from_conf_store(f'{key_prefix}>admin') is not None:
                counter = 0
                endpoints_in_confstore = []
                while self.cortx_conf.get(f'{key_prefix}>endpoints[{counter}]') is not None:
                    endpoints_in_confstore.append(self._get_value_from_conf_store(
                        f'{key_prefix}>endpoints[{counter}]'))
                    counter = counter + 1
                # Check endpoints
                if (endpoints_in_confstore != solution_config_services[service]['endpoints']):
                    raise CortxProvisionerError(errno.EINVAL,
                        f'{service} endpoints define in {self.cortx_conf_url} and '
                        f'{self.solution_conf_url} is not equal.')
        return 0

    def _validate_components(self):
        """Verify components defined in cluster.yaml is supported in constant file."""
        node_types = self._get_config('cluster>node_types')
        for node_type in node_types:
            component_list = node_type['components']
            for component in component_list:
                # check component_name exist in Utils Const cls.
                component_name = component['name']
                if component_name not in Const._value2member_map_:
                    raise CortxProvisionerError(errno.EINVAL,
                        f'{component_name} is not supported.')
                service_list = component.get('services')
                if service_list is not None:
                    self._validate_services(service_list, component_name)
        return 0

    def _validate_services(self, service_list, component_name):
        """Verify services defined in cluster.yaml is supported in constant file."""
        for service in service_list:
            # check if service name is define in utils const.py file.
            if service not in Const._value2member_map_:
                raise CortxProvisionerError(errno.EINVAL,
                    f'{service} is not supported.')
            # Verify service_name is define for the specific component.
            # Get all keys from constant file which has same 'service_name'.
            constant_service_keys = [
                key for key, enum_ele in Const.__members__.items() if enum_ele.value.lower() == service.lower()]
            if not any(component_name.upper() in key for key in constant_service_keys):
                Log.debug(f'"{service}" service defined in "{self.solution_conf_url}" for '
                    f'"{component_name}", is not supported.')
                raise CortxProvisionerError(errno.EINVAL,
                    f'Component "{component_name}" does not support service "{service}".')
        return 0

    def _get_config(self, key):
        """Read config value for key from config.yaml or cluster.yaml."""
        config_value = Conf.get(
            ConfigValidator._solution_index, key)
        if config_value is None:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'{key} key is unspecified for {self.solution_conf_url}')

        return config_value

    def _get_value_from_conf_store(self, key):
        """ Read config value from conf_store """

        config_value = self.cortx_conf.get(key)
        if config_value is None:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'{key} key is unspecified for {self.cortx_conf_url}')

        return config_value
