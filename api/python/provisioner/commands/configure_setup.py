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
# API for configuration of setup

import configparser
import logging

from enum import Enum
from typing import Type
from copy import deepcopy
from pathlib import Path

from . import CommandParserFillerMixin

from .validator import (
    NetworkParamsValidator,
    NodeParamsValidator,
    StorageEnclosureParamsValidator,
    ConfigValidator
)
from ..inputs import (
    METADATA_ARGPARSER,
    NoParams
)
from ..pillar import PillarIterable
from . import PillarSet

from ..values import (
    UNCHANGED, UNDEFINED
)
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
class ConfigureSetup(CommandParserFillerMixin):
    input_type: Type[NoParams] = NoParams
    _run_args_type = RunArgsConfigureSetup

    validate_map = {
        "cluster": NetworkParamsValidator,
        "node": NodeParamsValidator,
        "storage": StorageEnclosureParamsValidator
    }

    def _parse_params(self, input_data):
        params = {}
        for key in input_data.keys():
            val = key.split(".")

            if len(val) > 1:
                if val[-1] in [
                    'ip', 'user', 'secret', 'type', 'interfaces',
                    'private_interfaces', 'public_interfaces',
                    'gateway', 'netmask', 'public_ip', 'private_ip'
                ]:
                    # Node specific '.' separated params
                    # The '.' get replaced with '_'
                    params[f'{val[-2]}_{val[-1]}'] = input_data[key]

                elif 'cvg' in val and val[-1] in [
                    'data_devices', 'metadata_devices'
                ]:
                    if not params.get(val[-3]):
                        params[val[-3]] = []

                    if int(val[-2]) < len(params[val[-3]]):
                        params[val[-3]][int(val[-2])][val[-1]
                                                      ] = [input_data[key]]
                    else:
                        params[val[-3]].append(
                            {val[-1]: [input_data[key]]}
                        )
            else:
                params[val[-1]] = input_data[key]

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
        """Merge dict_1 to dict_2 recursively."""
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
        """
        Treat integer values in keys to arrays
        and update dict values

        """

        ret_val = []
        for key in contents.keys():
            if key.isdigit():
                ret_val.insert(int(key), contents[key])
            elif isinstance(contents[key], dict):
                ret_val = self._key_int_to_list(contents[key])
                if isinstance(ret_val, list):
                    if not isinstance(contents[key], list):
                        contents[key] = []
                    contents[key].extend(ret_val)
                    ret_val = contents
                else:
                    contents[key] = ret_val
                    ret_val = contents
            else:
                ret_val = contents
        return ret_val

    def _parse_input(self, input_data):
        """
        Parses content to string or arrays
        based on the category

        """
        kv_to_dict = dict()
        keys_of_type_list = [
            'interfaces', 'roles', 'data_devices', 'metadata_devices', 'cvg'
        ]
        for key in input_data.keys():
            if input_data.get(key) and "," in input_data.get(key):
                input_data[key] = [
                    element.strip() for element in input_data.get(key).split(",")
                ]

            elif any(k in key for k in keys_of_type_list):
                # special case single value as array
                # Need to fix this array having single value
                input_data[key] = [input_data.get(key)]

            else:
                if input_data.get(key):
                    if 'NONE' == input_data.get(key).upper():
                        input_data[key] = None
                    elif 'UNCHANGED' == input_data.get(key).upper():
                        input_data[key] = UNCHANGED
                    elif 'UNDEFINED' == input_data.get(key).upper():
                        input_data[key] = UNDEFINED
                    elif '' == input_data.get(key).upper():
                        input_data[key] = None
                    else:
                        input_data[key] = input_data.get(key)
                else:
                    input_data[key] = None

            if '.' in key:
                split_keys = key.split('.')
                kv_to_dict = self._dict_merge(
                    kv_to_dict,
                    self._list_to_dict(split_keys, input_data.get(key))
                )
                # logger.debug(f"KV to Dict ('.' separated): {kv_to_dict}")
            else:
                kv_to_dict[key] = input_data.get(key)
        kv_to_dict = self._key_int_to_list(kv_to_dict)
        logger.debug(f"KV to Dict: {kv_to_dict}")
        return kv_to_dict

    def run(self, path, number_of_nodes):  # noqa: C901
        if not Path(path).is_file():
            raise ValueError('config file is missing')

        validate = ConfigValidator()
        config = configparser.ConfigParser()
        config.read(path)

        final_dict = {'cluster': {}, 'storage': {}}

        logger.info("Updating salt data")

        content = {section: dict(config.items(section))
                   for section in config.sections()}
        logger.debug(
            f"Config data read from config.ini: \n{content}"
        )


        # Parse config sections
        parsed = validate._parse_sections(content)

        # Validate node count
        validate._validate_node_count(
            number_of_nodes, parsed
        )

        #validate blank values
        validate._validate_null_values(config)

        #validate network interfaces and data-matadata devices from config.ini
        validate._validate_config_interfaces(config)
        validate._validate_config_devices(config)

        # Process default sections
        # copy data from srvnode_default to individual server_node sections
        # delete srvnode_default section
        # Same with enclosure_default section

        srvnode_default = enclosure_default = None

        if parsed["srvnode_default"]:
            # 'default' sections found in config file

            srvnode_default = parsed["srvnode_default"]
            enclosure_default = parsed["enclosure_default"]
            del content["srvnode_default"]
            del content["enclosure_default"]

        for section in content.keys():

            if 'srvnode' in section and srvnode_default:
                tmp_section = deepcopy(srvnode_default)

            elif 'enclosure' in section and enclosure_default:
                tmp_section = deepcopy(enclosure_default)

            else:
                tmp_section = content[section]

            tmp_section.update(content[section])
            content[section] = tmp_section

            logger.debug(
                f"Processing content for {section}:{content[section]}"
            )
            input_type = ('node' if 'srvnode' in section
                          else 'storage' if 'enclosure' in section
                          else 'cluster')

            self._validate_params(input_type, content[section])
            content[section] = self._parse_input(content[section])
            if 'srvnode' in section:
                final_dict['cluster'].update({section: content[section]})
            elif 'enclosure' in section:
                final_dict['storage'].update({section: content[section]})
            else:
                final_dict.update({section: content[section]})

            logger.debug(
                f"Content to set for {section}: {content[section]}")
        logger.debug(f"Final dict to be set to pillar: {final_dict}")
        PillarSet(
            input_type=PillarIterable).run(
            PillarIterable(
                final_dict,
                expand=True))
        logger.info("Pillar data updated Successfully.")
