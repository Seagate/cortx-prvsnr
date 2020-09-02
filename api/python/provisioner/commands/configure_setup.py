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
import configparser
from typing import Type, List
from copy import deepcopy
from pathlib import Path

from ..inputs import (
    NetworkParams, ReleaseParams, StorageEnclosureParams
)
from .. import inputs
from ..vendor import attr
from ..pillar import PillarUpdater

from ..values import UNCHANGED
from . import (
    CommandParserFillerMixin
)
from ..config import (
    ALL_MINIONS
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsConfigureSetup:
    path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path to update pillar"
            }
        }
    )
    number_of_nodes: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Number of nodes"
            }
        }
    )


@attr.s(auto_attribs=True)
class SingleNodeParams:
    target_build: str = ReleaseParams.target_build
    cluster_ip: str = NetworkParams.cluster_ip
    mgmt_vip: str = NetworkParams.mgmt_vip
    primary_hostname: str = NetworkParams.primary_hostname
    primary_data_network_iface: List = NetworkParams.primary_data_network_iface
    primary_data_ip: str = NetworkParams.primary_data_ip
    primary_bmc_user: str = NetworkParams.primary_bmc_user
    primary_bmc_secret: str = NetworkParams.primary_bmc_secret
    controller_a_ip: str = StorageEnclosureParams.controller_a_ip
    controller_b_ip: str = StorageEnclosureParams.controller_b_ip
    controller_user: str = StorageEnclosureParams.controller_user
    controller_secret: str = StorageEnclosureParams.controller_secret

    _optional_param = ['primary_data_ip']

    def __attrs_post_init__(self):
        params = vars(self)
        optional_params = self._optional_param
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in optional_params:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class DualNodeParams(SingleNodeParams):
    secondary_hostname: str = NetworkParams.secondary_hostname
    secondary_data_network_iface: List = NetworkParams.secondary_data_network_iface  # noqa: E501
    secondary_bmc_user: str = NetworkParams.secondary_bmc_user
    secondary_bmc_secret: str = NetworkParams.secondary_bmc_secret
    secondary_data_ip: str = NetworkParams.secondary_data_ip

    _optional_param = SingleNodeParams._optional_param
    _optional_param.append('secondary_data_ip')

    def __attrs_post_init__(self):
        params = vars(self)
        optional_params = self._optional_param
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in optional_params:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class ConfigureSetup(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureSetup

    input_map = {"network": inputs.Network,
                 "release": inputs.Release,
                 "node": inputs.Node,
                 "storage_enclosure": inputs.StorageEnclosure}
    validate_map = {1: SingleNodeParams,
                    2: DualNodeParams}

    def _parse_input(self, input):
        for key in input:
            if input[key] and "," in input[key]:
                input[key] = [x.strip() for x in input[key].split(",")]

    def _validate_params(self, content, number_of_nodes):
        params = {}
        for section in content:
            params.update(content[section])
        self.validate_map[number_of_nodes](**params)

    def run(self, path, number_of_nodes):

        if not Path(path).is_file():
            raise ValueError('config file is missing')

        number_of_nodes = int(number_of_nodes)
        config = configparser.ConfigParser()
        config.read(path)
        logger.info("Updating salt data :")
        content = {section: dict(config.items(section)) for section in config.sections()}  # noqa: E501
        logger.debug(f"params data {content}")

        if number_of_nodes < 3:
            self._validate_params(content, number_of_nodes)

        targets = ALL_MINIONS
        count = deepcopy(number_of_nodes)

        for section in content:
            self._parse_input(content[section])
            if "node" in section:
                count = count - 1
                res = section.split(":")    # section will be node:srvnode-1
                targets = res[1]
                params = self.input_map[res[0]](**content[section])
            else:
                params = self.input_map[section](**content[section])
            pillar_updater = PillarUpdater(targets)
            pillar_updater.update(params)
            pillar_updater.apply()

        if number_of_nodes > 2 and count > 0:
            raise ValueError(f"Node information for {count} node missing")

        logger.info("Pillar data updated Successfully.")
