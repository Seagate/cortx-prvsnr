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
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging
from typing import Type, Union

from . import CommandParserFillerMixin, RunArgsEmpty

from .. import inputs, values

from .. import config
from ..errors import BadPillarDataError
from ..pillar import KeyPath, PillarKey, PillarResolver, PillarUpdater
from ..salt import function_run, local_minion_id
from ..vendor import attr


logger = logging.getLogger(__name__)


class OutputScheme:
    """Class which represents scheme for output result
    of GetSetupInfo.run method

    """
    _MAP = {
        config.NODES: int,
        config.SERVERS_PER_NODE: int,
        config.STORAGE_TYPE: str,
        config.SERVER_TYPE: str
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
        return config.NOT_AVAILABLE if value is None else formatter(value)


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
        config.NODES: "_count_servers_and_nodes",
        config.SERVERS_PER_NODE: "_count_servers_and_nodes",
        config.STORAGE_TYPE: "_get_storage_type",
        config.SERVER_TYPE: "_get_server_type"
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
                                targets=config.LOCAL_MINION)
        if salt_res:
            # it should have the following format
            # {"current node name": "physical"} or
            # {"current node name": "kvm"}, for example
            server_type = salt_res.popitem()[1]

            # TODO: EOS-12418-improvement:
            #  in future we may support other values of server type
            #  which salt provides
            res[config.SERVER_TYPE] = (
                    config.ServerType.PHYSICAL.value
                    if server_type == config.ServerType.PHYSICAL.value
                    else config.ServerType.VIRTUAL.value)

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
        get_result = PillarResolver(local_minion_id()).get([cluster_path])
        cluster_pillar = get_result[local_minion_id()][cluster_path]
        nodes_list = [
            node for node in cluster_pillar.keys()
            if 'srvnode-' in node
        ]

        cluster_key = PillarKey(cluster_path / 'cluster')
        type_key = PillarKey(cluster_path / 'node_type')

        pillar = PillarResolver(config.LOCAL_MINION).get(
            (cluster_key)
        )
        pillar = pillar.get(local_minion_id())  # type: dict

        for key in [cluster_key]:
            if not pillar[key] or pillar[key] is values.MISSED:
                raise BadPillarDataError(f'value for {key.keypath} '
                                         f'is not specified')

        cluster_info = pillar.get(type_key)
        node_list = [
            node for node in cluster_info
            if "srvnode-" in node
        ]

        if 1 == len(node_list):
            res[config.SERVERS_PER_NODE] = 1
        elif 2 == len(node_list):
            res[config.SERVERS_PER_NODE] = 2
            res[config.NODES] = (
                len(pillar[nodes_list])
            )
            res[config.STORAGE_SETS] = None
        elif (
            1 <= (len(node_list) // 3) and
            0 == (len(node_list) % 3)
        ):
            res[config.SERVERS_PER_NODE] = 1
            res[config.NODES] = (
                len(pillar[nodes_list])
            )
            res[config.STORAGE_SETS] = (
                len(pillar[nodes_list]) // 3
            )
        else:
            raise ValueError(
                f"Unsupported number of nodes '{len(node_list)}' in given cluster information."
            )

        return res

    @staticmethod
    def _get_storage_type_pillar_based():
        """
        Previous implementation of get_storage_method
        Can be used if command based approach failed
        :return:
        """
        res = dict()
        storage_path = KeyPath('storage')
        enclosure_id = "enclosure-1"
        storage_enclosure_type = PillarKey(
            storage_path / enclosure_id / 'type'
        )

        pillar = PillarResolver(config.LOCAL_MINION).get(
            (storage_enclosure_type,)
        )

        pillar = pillar.get(local_minion_id())  # type: dict

        if (not pillar[storage_enclosure_type] or
                pillar[storage_enclosure_type] is values.MISSED):
            raise BadPillarDataError('value for '
                                     f'{storage_enclosure_type.keypath} '
                                     'is not specified')

        res[config.STORAGE_TYPE] = pillar[storage_enclosure_type]

        return res

    @staticmethod
    def _update_storage_type_pillar(storage_type: str):
        """
        Update storage_type pillar by new value

        :param storage_type: new storage_type value for pillar
                            storage/enclosure_id/type
        :return:
        """
        storage_path = KeyPath('storage')
        enclosure_id = "enclosure-1"
        storage_enclosure_path = PillarKey(storage_path / enclosure_id)
        storage_enclosure_type = PillarKey(storage_enclosure_path / 'type')
        pillar_updater = PillarUpdater(config.ALL_MINIONS)
        pillar_updater.update((storage_enclosure_type, storage_type))
        pillar_updater.apply()

    def _get_storage_type(self):
        """
        Get storage type

        Algorithm:
        1. take storage_type/type pillar value. Filled from config.ini

        :return:
        """
        # Get storage type from pillar values
        try:
            return self._get_storage_type_pillar_based()
        except BadPillarDataError as e:
            logger.info("Pillar based approach for storage_type detection "
                        f"failed. Reason: {e}")

        self._update_storage_type_pillar(config.OTHER_STORAGE_TYPE)
        return {config.STORAGE_TYPE: config.OTHER_STORAGE_TYPE}

    # TODO: EOS-12418-improvement:
    #  Add support of arguments to retrieve just specified fields
    def run(self):
        """
        Base method to gather and return to user information about cluster
        installation

        :return:
        """
        aggregated_res = dict.fromkeys(config.SETUP_INFO_FIELDS, None)

        for field in config.SETUP_INFO_FIELDS:
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
            for key in (
                    res.keys() & set(
                        k for k, v in aggregated_res.items() if v is None)):
                aggregated_res[key] = res.get(key)

        return self._format_output(aggregated_res)
