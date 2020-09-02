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
from typing import Type
from copy import deepcopy
from pathlib import Path

from .. import inputs
from ..vendor import attr
from ..pillar import PillarUpdater

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
class ConfigureSetup(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureSetup

    # TODO : https://jts.seagate.com/browse/EOS-11741
    # Improve optional and mandatory param validation
    SINGLE_PARAM = [
        "target_build",
        "controller_a_ip",
        "controller_b_ip",
        "controller_user",
        "controller_secret",
        "primary_hostname",
        "primary_data_network_iface",
        "primary_bmc_user",
        "primary_bmc_secret"]
    DUAL_PARAM = [
        "target_build",
        "controller_a_ip",
        "controller_b_ip",
        "controller_user",
        "controller_secret",
        "primary_hostname",
        "primary_data_network_iface",
        "primary_bmc_user",
        "primary_bmc_secret",
        "secondary_hostname",
        "secondary_data_network_iface",
        "secondary_bmc_user",
        "secondary_bmc_secret"]

    input_map = {"network": inputs.Network,
                 "release": inputs.Release,
                 "node": inputs.Node,
                 "storage_enclosure": inputs.StorageEnclosure}
    validate_map = {1: SINGLE_PARAM,
                    2: DUAL_PARAM}

    def _parse_input(self, input):
        for key in input:
            if input[key] and "," in input[key]:
                input[key] = [x.strip() for x in input[key].split(",")]

    def _validate_params(self, content, number_of_nodes):
        params = self.validate_map[number_of_nodes]
        mandatory_param = deepcopy(params)
        for section in content:
            for key in content[section]:
                if key in mandatory_param:
                    if content[section][key]:
                        mandatory_param.remove(key)
        if len(mandatory_param) > 0:
            raise ValueError(f"Mandatory param missing {mandatory_param}")

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
