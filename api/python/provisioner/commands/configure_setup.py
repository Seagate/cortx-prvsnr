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

import configparser
import logging

from enum import Enum
from typing import Type, List
from copy import deepcopy
from pathlib import Path

from . import CommandParserFillerMixin

from ..inputs import (
    METADATA_ARGPARSER,
    NetworkParams, NodeParams, NoParams,
    ReleaseParams, StorageEnclosureParams
)

from . import PillarSet
from .grains_get import GrainsGet
from ..salt import local_minion_id

from ..values import UNCHANGED
from ..vendor import attr


logger = logging.getLogger(__name__)


class SetupType(Enum):
    SINGLE = "single"
    DUAL = "dual"
    GENERIC = "generic"
    THREE_NODE = "3_node"
    LDR_R1 = "LDR-R1"
    LDR_R2 = "LDR-R2"


class RunArgsConfigureSetupAttrs:
    path: str = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': "config path to update pillar"
            }
        }
    )
    setup_type: str = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': "the type of the setup",
                'choices': [st.value for st in SetupType]
            }
        },
        default=SetupType.SINGLE.value,
        # TODO EOS-12076 better validation
        converter=(lambda v: SetupType(v))
    )
    number_of_nodes: int = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': "No of nodes in cluster"
            }
        },
        converter=int
    )


@attr.s(auto_attribs=True)
class RunArgsConfigureSetup:
    path: str = RunArgsConfigureSetupAttrs.path
    number_of_nodes: int = RunArgsConfigureSetupAttrs.number_of_nodes

    # FIXME number of nodes might be the same for different setup types
    setup_type: str = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        pass


@attr.s(auto_attribs=True)
class NetworkParamsValidation:
    cluster_ip: str = NetworkParams.cluster_ip
    mgmt_vip: str = NetworkParams.mgmt_vip
    _optional_param = ['cluster_ip', 'mgmt_vip']

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class ReleaseParamsValidation:
    target_build: str = ReleaseParams.target_build
    _optional_param = []

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class StorageEnclosureParamsValidation:
    type: str = StorageEnclosureParams.type
    primary_ip: str = StorageEnclosureParams.primary_ip
    secondary_ip: str = StorageEnclosureParams.secondary_ip
    controller_user: str = StorageEnclosureParams.controller_user
    controller_secret: str = StorageEnclosureParams.controller_secret
    controller_type: str = StorageEnclosureParams.controller_type
    _optional_param = [
        'controller_type'
    ]

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        # FIXME why we allow any params for the following types?
        types = ['JBOD', 'virtual', 'RBOD', 'other']
        if params['type'] in types:
            return
        missing_params = []
        for param, value in params.items():
            if (
                value == UNCHANGED and
                param not in self._optional_param and
                params['type'] == 'RBOD'
            ):
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class NodeParamsValidation:
    bmc_user: str = NodeParams.bmc_user
    bmc_secret: str = NodeParams.bmc_secret
    data_gateway: str = NodeParams.data_gateway
    data_netmask: str = NodeParams.data_netmask
    data_private_interfaces: List = NodeParams.data_private_interfaces
    data_private_ip: str = NodeParams.data_private_ip
    data_public_interfaces: List = NodeParams.data_public_interfaces
    data_public_ip: str = NodeParams.data_public_ip
    hostname: str = NodeParams.hostname
    mgmt_gateway: str = NodeParams.mgmt_gateway
    mgmt_interfaces: List = NodeParams.mgmt_interfaces
    mgmt_netmask: str = NodeParams.mgmt_netmask
    mgmt_public_ip: str = NodeParams.mgmt_public_ip
    roles: List = NodeParams.roles
    cvg: List = NodeParams.cvg

    _optional_param = [
        'data_public_ip',
        'roles',
        'data_netmask',
        'data_gateway',
        'data_private_ip',
        'mgmt_interfaces',
        'mgmt_public_ip',
        'mgmt_netmask',
        'mgmt_gateway',
        'cvg'
    ]

    if (
        not 'physical' in GrainsGet().run(
            'virtual',
            targets=local_minion_id()
        )[local_minion_id()]['virtual']
    ):
        _optional_param.extend([
            'bmc_user',
            'bmc_secret'
        ])

    def __attrs_post_init__(self):
        params = attr.asdict(self)

        # If storage.cvg.metadata or storage.cvg.data is specified,
        # check entry for the other.
        for data_set in params.get('cvg'):
            logger.debug(f"DataSet being processed for CVG keys: {data_set}")
            if (
                data_set.get('data_devices') and
                (
                    (not data_set.get('metadata_devices')) or
                    (data_set.get('metadata_devices') == UNCHANGED) or
                    (data_set.get('metadata_devices') == '')
                )
            ):
                raise ValueError(
                    "List of data is specified. "
                    "However, list of metadata is unspecified."
                )
            elif (
                data_set.get('metadata_devices') and
                (
                    (not data_set.get('data_devices')) or
                    (data_set.get('data_devices') == UNCHANGED) or
                    (data_set.get('data_devices') == '')
                )
            ):
                raise ValueError(
                    "List of metadata is specified. "
                    "However, list of data is unspecified."
                )

        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class ConfigureSetup(CommandParserFillerMixin):
    input_type: Type[NoParams] = NoParams
    _run_args_type = RunArgsConfigureSetup

    validate_map = {
        "cluster": NetworkParamsValidation,
        "node": NodeParamsValidation,
        "storage": StorageEnclosureParamsValidation
    }


    def _parse_params(self, input):
        params = {}
        for key in input.keys():
            val = key.split(".")

            if len(val) > 1:
                if val[-1] in [
                    'ip', 'user', 'secret', 'type', 'interfaces',
                    'private_interfaces', 'public_interfaces',
                    'gateway', 'netmask', 'public_ip', 'private_ip'
                ]:
                    # Node specific '.' separated params
                    # The '.' get replaced with '_'
                    params[f'{val[-2]}_{val[-1]}'] = input[key]
                elif val[-1] in [
                    'data_devices', 'metadata_devices'
                ]:
                    if not params.get(val[-3]):
                        params[val[-3]] = []

                    if int(val[-2]) < len(params[val[-3]]):
                        params[val[-3]][int(val[-2])][val[-1]] = [input[key]]
                    else:
                        params[val[-3]].append(
                            { val[-1]: [input[key]] }
                        )
            else:
                params[val[-1]] = input[key]

        logger.debug(f"Parsed params: {params}")
        return params


    def _validate_params(self, input_type, content):
        params = self._parse_params(content)
        logger.debug(f"Validating {input_type}::{params}")
        self.validate_map[input_type](**params)


    def _list_to_dict(self, inp_list, last_node_val: None):
        """Recursively convert a list to a nested dictionary

        inp_list: List to be converted to a Python dict
        last_node_val: value to be assigned to last node in tree.
        """
        new_dict = dict()
        if len(inp_list) > 1:
            # Recurse
            new_dict[inp_list[0]] = self._list_to_dict(
                inp_list[1:],
                last_node_val
            )
        else:
            new_dict[inp_list[0]] = last_node_val

        logger.debug(f"Section list to Dict: {new_dict}")
        return new_dict


    def _dict_merge(self, dict_1, dict_2):
        """Merge dict_1 to dict_2 recursively"""
        for key in dict_2.keys():
            if key in dict_1:
                if (
                    isinstance(dict_1[key], dict) and
                    isinstance(dict_2[key], dict)
                ):
                    # Recurse
                    logger.debug(f"recursing: {dict_1}::{dict_2}")
                    self._dict_merge(dict_1[key], dict_2[key])
            else:
                # Create new dictionary node
                logger.debug(f"dict node create: {dict_1}::{dict_2}")
                dict_1[key] = dict_2[key]

        logger.debug(f"The merged dictionaries: {dict_1}")
        return dict_1


    def _key_int_to_list(self, contents):
        """Treat integer values in keys to arrays and update dict values"""
        ret_val = None
        for key in contents.keys():
            if key.isdigit():
                ret_val = [contents[key]]
            elif isinstance(contents[key], dict):
                tmp_var = self._key_int_to_list(contents[key])
                if isinstance(tmp_var, inp_list):
                    if not isinstance(contents[key], inp_list):
                        contents[key] = []
                    contents[key].append(tmp_var)
            else:
                ret_val = contents

        return ret_val


    def _parse_input(self, input):
        kv_to_dict = dict()
        for key in input.keys():
            if "," in input[key]:
                input[key] = [element.strip() for element in input[key].split(",")]
            elif (
                'interfaces' in key or
                'roles' in key or
                'data_devices' in key or
                'metadata_devices' in key
            ):
                # special case single value as array
                # Need to fix this array having single value
                input[key] = [input[key]]
            else:
                if input.get(key):
                    if input[key] == 'None':
                        input[key] = ''
                    else:
                        input[key] = {input[key]}
                else:
                    input[key] = UNCHANGED

            if '.' in key:
                split_keys = key.split('.')
                kv_to_dict = self._dict_merge(
                    kv_to_dict,
                    self._list_to_dict(split_keys, input[key])
                )
                # logger.debug(f"KV to Dict ('.' separated): {kv_to_dict}")
            else:
                kv_to_dict[key] = input[key]

        kv_to_dict = self._key_int_to_list(kv_to_dict)
        logger.debug(f"KV to Dict: {kv_to_dict}")
        return kv_to_dict


    def run(self, path, number_of_nodes):  # noqa: C901
        if not Path(path).is_file():
            raise ValueError('config file is missing')

        config = configparser.ConfigParser()
        config.read(path)
        logger.info("Updating salt data")
        content = {section: dict(config.items(section)) for section in config.sections()}  # noqa: E501
        logger.debug(f"Data from config.ini: \n{content}")

        input_type = None
        pillar_type = None
        node_list = []
        srvnode_count = enclosure_count = int(number_of_nodes)

        # Process srvnode_default section
        # copy data from srvnode_default to individual server_node sections
        # delete srvnode_default section
        srvnode_default = enclosure_default = None
        if content.get("srvnode_default"):
            srvnode_default = content.get("srvnode_default")
            del content["srvnode_default"]
        if content.get("enclosure_default"):
            enclosure_default = content.get("enclosure_default")
            del content["enclosure_default"]

        logger.debug(f"Content ready for unification: \n{content}")
        for section in content.keys():
            if (
                'srvnode' in section and
                srvnode_default
            ):
                tmp_section = srvnode_default
            elif (
                'enclosure' in section and
                enclosure_default
            ):
                tmp_section = enclosure_default
            else:
                tmp_section = content[section]

            tmp_section.update(content[section])
            content[section] = tmp_section
            logger.debug(f"Content {section}::{content[section]}")

        logger.debug(f"Unified sections: \n{content}")

        for section in content.keys():
            logger.debug(
                f"Processing section: {section}\n"
                f"Processing content: {content[section]}"
            )

            if 'srvnode' in section:
                input_type = 'node'
                pillar_type = f'cluster/{section}'
                srvnode_count = srvnode_count - 1
            elif 'enclosure' in section:
                input_type = 'storage'
                pillar_type = f'storage/{section}'
                enclosure_count = enclosure_count - 1

            self._validate_params(input_type, content[section])
            content[section] = self._parse_input(content[section])

            # logger.debug(f"Dictionarized contents: {content}")
            PillarSet().run(f"{pillar_type}", content[section])

        if srvnode_count > 0:
            raise ValueError(f"Node information for {srvnode_count} node missing")
        if enclosure_count > 0:
            raise ValueError(f"Enclosure information for {enclosure_count} node missing")

        logger.info("Pillar data updated Successfully.")
