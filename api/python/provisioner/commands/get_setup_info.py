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
from typing import Type

from . import CommandParserFillerMixin, RunArgsEmpty

from .. import (
    config,
    inputs, values
)
from ..config import LOCAL_MINION
from ..errors import BadPillarDataError
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import function_run
from ..vendor import attr


logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Class-enumeration for supported and existing storage types"""

    VIRTUAL = "virtual"
    # standard enclosure with 5 units with 84 disks
    ENCLOSURE = "5u84"
    PODS = "PODS"


class ServerType(Enum):
    """Class-enumeration which represents possible server types"""

    VIRTUAL = "virtual"
    PHYSICAL = "physical"


class ControllerTypes(Enum):
    """Class-enumeration for controller type's values"""
    GALLIUM = "gallium"
    INDIUM = "indium"
    SATI = "sati"


# TODO: maybe needed to move to config.py
# Constant block for setup info fields
NODES = "nodes"
SERVERS_PER_NODE = "servers_per_node"
STORAGE_TYPE = "storage_type"
SERVER_TYPE = "server_type"

SETUP_INFO_FIELDS = (NODES, SERVERS_PER_NODE, STORAGE_TYPE, SERVER_TYPE)

NOT_AVAILABLE = "N/A"


# TODO: in CSM we use schematics third-party library
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
    def field_formatter(cls, key, value):
        if value is None:
            return f'"{key}": "{NOT_AVAILABLE}"'
        elif cls._MAP.get(key) == int:
            return f'"{key}": {int(value)}'
        elif cls._MAP.get(key) == str:
            return f'"{key}": "{str(value)}"'


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

        return "\n".join(OutputScheme.field_formatter(key, value)
                         for key, value in res_dict.items())

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
                continue  # field value is already known form previous steps

            handler_name = self.FIELD_HANDLERS.get(field, None)
            if handler_name is None:
                raise ValueError(f"There are no handlers for {field} field")

            handler = getattr(self, handler_name, None)

            if any((handler is None, not callable(handler))):
                raise ValueError(f"Handler {handler} is not implemented "
                                 f"for field {field}")

            res = handler()
            # NOTE: one method can determine several fields
            # Update only fields which are not
            for key in res.keys() & set(k for k, v in
                                        filter(lambda x: x[1] is None,
                                               aggregated_res.items())):
                aggregated_res[key] = res.get(key)

        return self._format_output(aggregated_res)

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
