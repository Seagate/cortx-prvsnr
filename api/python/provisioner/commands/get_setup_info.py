#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging
from enum import Enum
from typing import Type, Union

from . import CommandParserFillerMixin, RunArgsEmpty

from .. import (
    config,
    inputs, values
)
from ..config import (LOCAL_MINION, NODES, SERVERS_PER_NODE, STORAGE_TYPE,
                      SERVER_TYPE, NOT_AVAILABLE, ServerType, ControllerTypes,
                      StorageType, SETUP_INFO_FIELDS
                      )
from ..errors import BadPillarDataError
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import function_run
from ..vendor import attr


logger = logging.getLogger(__name__)


class OutputScheme:
    """Class which represents scheme for output result
    of GetSetupInfo.run method

    """
    _MAP = {
        NODES: int,
        SERVERS_PER_NODE: int,
        STORAGE_TYPE: str,
        SERVER_TYPE: str
    }

    @classmethod
    def format(cls, key: str, value: Union[str, int]) -> Union[str, int]:
        """
        Apply to key's values `cls._MAP` handlers

        :param key: key name. Should be listed in `cls._MAP`
        :param value: key's value to which `cls._MAP` handler will be applied
        :return: formatted key's value according to `cls._MAP` handlers
        """
        formatter = cls._MAP.get(key, None)
        if formatter is None:
            raise ValueError(f"Format handler for field {key} is not defined")
        return formatter(value)


@attr.s(auto_attribs=True)
class GetSetupInfo(CommandParserFillerMixin):
    """General class-wrapper for obtaining cluster setup information"""

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsEmpty

    # NOTE: it is possible that for field we can have different
    # methods/handlers which determine field's value
    # TODO: each field can support numerous handlers
    # TODO: in case of numerous handlers per field need to ensure that one
    #       handler runs once
    FIELD_HANDLERS = {
        NODES: "_count_minions",
        SERVERS_PER_NODE: "_get_servers_per_node",
        STORAGE_TYPE: "_get_storage_type",
        SERVER_TYPE: "_get_server_type"
    }

    @staticmethod
    def _format_output(res_dict: dict):
        """
        Format result dict data to desired output like
            <key1>: <value1>
            <key2>: <value2>

        :param res_dict: result dict
        :return:
        """
        if not isinstance(res_dict, (dict,)):
            raise ValueError("Input parameter should type of dict")

        return {k: OutputScheme.format(k, v) for k, v in res_dict.items()}

    def _count_minions(self):
        """
        Private method to count active (registered) minions

        :return:
        """
        res = dict()

        return res

    def _get_server_type(self):
        """
        Private method to determine server type

        :return:
        """
        res = dict()

        salt_res = function_run('grains.get', fun_args=['virtual'],
                                targets=LOCAL_MINION)
        if salt_res:
            # it should have the following format
            # {"current node name": "physical"} or
            # {"current node name": "kvm"}, for example
            server_type = salt_res.popitem()[1]

            # TODO: in future we may support other values of server type
            #  which salt provides
            res[SERVER_TYPE] = (ServerType.PHYSICAL.value
                                if server_type == ServerType.PHYSICAL.value
                                else ServerType.VIRTUAL.value)

        return res

    def _get_servers_per_node(self):
        """
        Private method to obtain number of servers per node

        :return:
        """
        res = dict()

        cluster_path = KeyPath('cluster')
        node_list_key = PillarKey(cluster_path / 'node_list')
        type_key = PillarKey(cluster_path / 'type')

        pillar = PillarResolver(LOCAL_MINION).get((node_list_key, type_key))

        pillar = next(iter(pillar.values()))  # type: dict

        for key in (node_list_key, type_key):
            if (not pillar[key] or
                    pillar[key] is values.MISSED):
                raise BadPillarDataError(f'value for {key.keypath} '
                                         f'is not specified')

        # TODO: improve logic to determine servers_per_node field using
        #  both: cluster/node_list and cluster/type values

        res[SERVERS_PER_NODE] = len(pillar[node_list_key])

        return res

    def _get_storage_type(self):
        """
        Private method to determine storage type

        :return:
        """
        res = dict()
        controller_pi_path = KeyPath('storage_enclosure/controller')
        controller_type = PillarKey(controller_pi_path / 'type')

        pillar = PillarResolver(LOCAL_MINION).get((controller_type,))

        pillar = next(iter(pillar.values()))  # type: dict

        if (not pillar[controller_type] or
                pillar[controller_type] is values.MISSED):
            raise BadPillarDataError(f'value for {controller_type.keypath} '
                                     f'is not specified')

        if pillar[controller_type] == ControllerTypes.GALLIUM.value:
            res[STORAGE_TYPE] = StorageType.ENCLOSURE.value

        # TODO: implement for other types: virtual, JBOD, PODS

        return res

    # TODO: Add support of arguments to retrieve just specified fields
    def run(self):
        """
        Base method to gather and return to user information about cluster
        installation

        :return:
        """
        aggregated_res = dict.fromkeys(SETUP_INFO_FIELDS, None)

        for field in SETUP_INFO_FIELDS:
            if aggregated_res.get(field) is not None:
                continue  # field value is already known from previous steps

            # NOTE: be sure, we don't validate the following possible
            # conditions:
            # * class may not have implemented expected handlers
            # * some fields may have no assigned handlers
            # * some fields can be not listed in FIELD_HANDLERS
            handler = getattr(self, self.FIELD_HANDLERS.get(field))

            res = handler()
            # NOTE: one method can determine several fields
            # Update only unknown fields
            for key in res.keys() & set(k for k, v in
                                        filter(lambda x: x[1] is None,
                                               aggregated_res.items())):
                aggregated_res[key] = res.get(key)

        return self._format_output(aggregated_res)
