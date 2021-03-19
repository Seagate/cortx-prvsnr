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
from copy import deepcopy
from pathlib import Path
from typing import Type

from . import (
    CommandParserFillerMixin,
    PillarSet
)
from .. import inputs
from ..config import (
    NODE_DEFAULT,
    STORAGE_DEFAULT,
    CLUSTER, NODE,
    STORAGE
)
from ..salt import local_minion_id

from ..validate import (
    ValidateSetup,
    ClusterParamsValidation,
    StorageParamsValidation,
    NodeParamsValidation,
)
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
            inputs.METADATA_ARGPARSER: {
                'help': "config path to update pillar"
            }
        }
    )
    setup_type: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
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
            inputs.METADATA_ARGPARSER: {
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
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureSetup

    # "cluster" : Validates common cluster params like cluster_ip
    # "srvnode-default" and "srvnode" : Validates each node sections params
    # "storage-default" and "storage" : Validates each storage sections params

    validate_map = {f'{CLUSTER}': ClusterParamsValidation,
                    f'{NODE}': NodeParamsValidation,
                    f'{NODE_DEFAULT}': NodeParamsValidation,
                    f'{STORAGE}': StorageParamsValidation,
                    f'{STORAGE_DEFAULT}': StorageParamsValidation}

    @staticmethod
    def _parse_params(param_data):
        params = {}
        for key in param_data:
            val = key.split(".")
            conf_values = [
                'ip', 'user', 'secret', 'type', 'gateway',
                'netmask', 'public_ip', 'private_ip',
                'public_interfaces', 'private_interfaces',
                'id', 'roles', 'devices', 'interfaces'
            ]

            if len(val) > 1 and val[-1] in conf_values:
                params[f'{val[-2]}_{val[-1]}'] = param_data[key]

            else:
                params[val[-1]] = param_data[key]

        logger.debug(f"Params generated: {params}")
        return params

    def _validate_params(self, input_type, content):
        params = self._parse_params(content)
        self.validate_map[input_type](**params)

    @staticmethod
    def _parse_input(input_data):
        for key in input_data:
            keys_of_type_list = [
                'interfaces', 'devices', 'roles'
            ]
            if input_data[key] and "," in input_data[key]:
                value = [x.strip() for x in input_data[key].split(",")]
                value = ','.join(value)
                input_data[key] = [value]

            elif key in keys_of_type_list:
                input_data[key] = f'[\"{input_data[key]}\"]'

            else:
                if input_data[key]:
                    if input_data[key] == 'None':
                        input_data[key] = ''
                    else:
                        input_data[key] = input_data[key]
                else:
                    input_data[key] = UNCHANGED

    @staticmethod
    def _parse_pillar_key(key):
        pillar_key = deepcopy(key)
        return pillar_key.replace(".", "/")

    def _update_pillar_data(self, set_content, pillar_type):
        """
        Set pillar data.

        Config content of default sections will be applied
        across all nodes.

        """
        for pillar_key in set_content:
            key_to_set = f'{pillar_type}/{self._parse_pillar_key(pillar_key)}'
            value_to_set = f'{set_content[pillar_key]}'

            PillarSet().run(
                key_to_set,
                value_to_set,
                targets=local_minion_id()
            )

    def run(self, path, number_of_nodes):  # noqa: C901

        logger.debug(
            f"Number of nodes received to configure: {number_of_nodes}"
        )
        validate = ValidateSetup()

        if not Path(path).is_file():
            logger.error(
               "config file is mandatory for setup configure. "
               "Please provide a valid config file path. "
            )
            raise ValueError('config file is missing')

        config = configparser.ConfigParser()
        config.read(path)
        logger.info("Updating salt data..")
        content = {section: dict(config.items(section))
                   for section in config.sections()}
        logger.debug(
            f"Config data read from provided file: {content}"
        )

        # Config sections segregated default-wise, node-wise.
        parsed = validate._parse_nodes(content)
        pillar_map = parsed.pop("pillar_map")

        # TB merged: validate_node_count

        for section in parsed:
            input_type = section
            set_content = deepcopy(parsed[section])

            if f'{NODE_DEFAULT}' in parsed:
                # 'default' sections found in config file
                parse_section = (
                   f'{NODE}' if section == f'{NODE_DEFAULT}'
                   else f'{STORAGE}' if section == f'{STORAGE_DEFAULT}'
                   else None
                )

            else:
                # 'default' sections NOT found in config file
                parse_section = (
                   None if f'{CLUSTER}' in section
                   else section
                )

            if parse_section:
                # All sections except "cluster" are handled here

                parse_data = parsed[parse_section]
                for each_node in parse_data:
                    pillar_type = f'{pillar_map[parse_section]}/{each_node}'
                    if "default" in section:

                        # Contents of 'default' sections will be
                        # updated with node data and applied to all nodes
                        set_content.update(parse_data[each_node])
                    else:
                        set_content = parse_data[each_node]

                    self._validate_params(input_type, set_content)
                    self._parse_input(set_content)
                    self._update_pillar_data(set_content, pillar_type)

            elif (not parse_section) and (section == f'{CLUSTER}'):
                pillar_type = pillar_map[section]
                self._validate_params(input_type, set_content)
                self._parse_input(set_content)
                self._update_pillar_data(set_content, pillar_type)

        if content.get('cluster', None):
            if content.get('cluster').get('cluster_ip', None):

                PillarSet().run(
                    "s3clients/ip",
                    f"{content.get('cluster').get('cluster_ip')}",
                    targets=local_minion_id()
                )

        logger.info("Pillar data updated Successfully.")
