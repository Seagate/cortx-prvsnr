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
    inputs
)
from ..config import LOCAL_MINION
from ..salt import function_run
from ..vendor import attr


logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Class-enumeration for supported and existing storage types"""

    VIRTUAL = "virtual"
    # standard enclosure with 5 units with 84 disks per unit
    ENCLOSURE = "5u84"
    PODS = "PODS"


class ServerType(Enum):
    """Class-enumeration which represents possible server types"""

    VIRTUAL = "virtual"
    PHYSICAL = "physical"


# TODO: maybe needed to move to config.py
# Constant block for setup info fields
NODES = "nodes"
SERVERS_PER_NODE = "servers_per_node"
STORAGE_TYPE = "storage_type"
SERVER_TYPE = "server_type"

SETUP_INFO_FIELDS = (NODES, SERVERS_PER_NODE, STORAGE_TYPE, SERVER_TYPE)

NOT_AVAILABLE = "N/A"


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

        return "\n".join(f"{key}: {value}" for key, value in res_dict.items())

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

        return res

    def _get_storage_type(self):
        """
        Private method to determine storage type

        :return:
        """
        res = dict()

        return res
