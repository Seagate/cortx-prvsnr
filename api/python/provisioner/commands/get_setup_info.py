#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

import logging
from typing import Type, Union

from . import CommandParserFillerMixin, RunArgsEmpty
from .configure_setup import SetupType

from .. import inputs, values

from ..config import (NODES, SERVERS_PER_NODE, STORAGE_TYPE,
                      SERVER_TYPE, NOT_AVAILABLE, ServerType, ControllerTypes,
                      StorageType, SETUP_INFO_FIELDS, LOCAL_MINION
                      )
from ..errors import BadPillarDataError
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import function_run, local_minion_id
from ..vendor import attr


logger = logging.getLogger(__name__)

# TODO: EOS-12418-improvement:
#  for some reason this setup type is not listed in
#  configure_setup.SetupType but can be set in
#  VM configuration cluster.sls file
SETUP_TYPE = "ldr-r1"


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
        return NOT_AVAILABLE if value is None else formatter(value)


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
        NODES: "_count_servers_and_nodes",
        SERVERS_PER_NODE: "_count_servers_and_nodes",
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

            # TODO: EOS-12418-improvement:
            #  in future we may support other values of server type
            #  which salt provides
            res[SERVER_TYPE] = (ServerType.PHYSICAL.value
                                if server_type == ServerType.PHYSICAL.value
                                else ServerType.VIRTUAL.value)

        return res

    def _count_servers_and_nodes(self):
        """
        Private method to obtain number of nodes (enclosures)
        and servers per node

        NOTE: this method counts both NODES and SERVERS_PER_NODE fields

        :return:
        """
        res = dict()

        cluster_path = KeyPath('cluster')
        node_list_key = PillarKey(cluster_path / 'node_list')
        type_key = PillarKey(cluster_path / 'type')

        pillar = PillarResolver(LOCAL_MINION).get((node_list_key, type_key))

        pillar = pillar.get(local_minion_id())  # type: dict

        for key in (node_list_key, type_key):
            if (not pillar[key] or
                    pillar[key] is values.MISSED):
                raise BadPillarDataError(f'value for {key.keypath} '
                                         f'is not specified')

        storage_type = pillar.get(type_key)
        if storage_type == SetupType.SINGLE.value:
            res[SERVERS_PER_NODE] = 1
        elif storage_type == SetupType.DUAL.value:
            res[SERVERS_PER_NODE] = 2
        elif storage_type.lower() == SETUP_TYPE:
            # TODO: EOS-12418-improvement:
            #  does this value can be used in real configuration?
            res[SERVERS_PER_NODE] = 2
        else:
            raise ValueError(f"Unsupported value '{storage_type}' for "
                             f"'cluster/type' pillar value")

        # Assumption: number of nodes in 'cluster/node_list' should be
        # multiple by 'cluster/type'
        if (len(pillar[node_list_key]) % res[SERVERS_PER_NODE]) != 0:
            raise ValueError(f"Unknown cluster configuration: "
                             f"total number of nodes(servers) = "
                             f"{pillar[node_list_key]}\n"
                             f"cluster type = {storage_type}")

        res[NODES] = len(pillar[node_list_key]) // res[SERVERS_PER_NODE]

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

        pillar = pillar.get(local_minion_id())  # type: dict

        if (not pillar[controller_type] or
                pillar[controller_type] is values.MISSED):
            raise BadPillarDataError(f'value for {controller_type.keypath} '
                                     f'is not specified')

        if pillar[controller_type] == ControllerTypes.GALLIUM.value:
            res[STORAGE_TYPE] = StorageType.ENCLOSURE.value
        elif pillar[controller_type] == ControllerTypes.INDIUM.value:
            res[STORAGE_TYPE] = StorageType.PODS.value

        # TODO: EOS-12418-improvement:
        #  implement for other types: virtual, JBOD

        return res

    # TODO: EOS-12418-improvement:
    #  Add support of arguments to retrieve just specified fields
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
            for key in (res.keys() & set(k for k, v in aggregated_res.items()
                                         if v is None)):
                aggregated_res[key] = res.get(key)

        return self._format_output(aggregated_res)
