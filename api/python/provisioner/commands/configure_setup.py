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
import configparser
from enum import Enum
from typing import Type
from copy import deepcopy
from pathlib import Path

from .. import inputs
from ..vendor import attr
from ..pillar import PillarUpdater

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


class SetupType(Enum):
    SINGLE = "single"
    DUAL = "dual"


@attr.s(auto_attribs=True)
class RunArgsConfigureSetup:
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
                'help': "type of setup",
                'choices': [st.value for st in SetupType]
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
                 "storage_enclosure": inputs.StorageEnclosure}
    validate_map = {SetupType.SINGLE.value: SINGLE_PARAM,
                    SetupType.DUAL.value: DUAL_PARAM}

    def _parse_input(self, input):
        for key in input:
            if input[key] and "," in input[key]:
                input[key] = [x.strip() for x in input[key].split(",")]

    def _validate_params(self, content, setup_type):
        params = self.validate_map[setup_type]
        mandatory_param = deepcopy(params)
        for section in content:
            for key in content[section]:
                if key in mandatory_param:
                    if content[section][key]:
                        mandatory_param.remove(key)
        if len(mandatory_param) > 0:
            raise ValueError(f"Mandatory param missing {mandatory_param}")

    def run(self, path, setup_type):

        if not Path(path).is_file():
            raise ValueError('config file is missing')

        config = configparser.ConfigParser()
        config.read(path)
        logger.info("Updating salt data :")
        content = {section: dict(config.items(section)) for section in config.sections()}  # noqa: E501
        logger.debug(f"params data {content}")
        self._validate_params(content, setup_type)

        for section in content:
            self._parse_input(content[section])
            params = self.input_map[section](**content[section])
            pillar_updater = PillarUpdater()
            pillar_updater.update(params)
            pillar_updater.apply()

        logger.info("Pillar data updated Successfully.")
