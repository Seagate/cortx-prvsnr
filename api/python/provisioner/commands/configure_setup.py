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
from enum import Enum
from typing import Type, List
from copy import deepcopy
from pathlib import Path

from ..inputs import (
    NetworkParams, ReleaseParams, StorageEnclosureParams,
    NodeNetworkParams
)
from .. import inputs
from ..vendor import attr

from ..utils import run_subprocess_cmd

from ..values import UNCHANGED
from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


class SetupType(Enum):
    SINGLE = "single"
    DUAL = "dual"
    GENERIC = "generic"


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
        default=SetupType.GENERIC.value,
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
        if self.number_of_nodes == 1:
            self.setup_type = SetupType.SINGLE
        elif self.number_of_nodes == 2:
            self.setup_type = SetupType.DUAL
        else:
            self.setup_type = SetupType.GENERIC


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
    storage_type: str = StorageEnclosureParams.storage_type
    primary_mc_ip: str = StorageEnclosureParams.primary_mc_ip
    secondary_mc_ip: str = StorageEnclosureParams.secondary_mc_ip
    controller_user: str = StorageEnclosureParams.controller_user
    controller_secret: str = StorageEnclosureParams.controller_secret
    _optional_param = []

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        if params['storage_type'] == 'JBOD':
            return
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class NodeParamsValidation:
    hostname: str = NodeNetworkParams.hostname
    is_primary: str = NodeNetworkParams.is_primary
    data_nw_iface: List = NodeNetworkParams.data_nw_iface
    public_ip_addr: str = NodeNetworkParams.public_ip_addr
    data_nw_netmask: str = NodeNetworkParams.data_nw_netmask
    data_nw_gateway: str = NodeNetworkParams.data_nw_gateway
    pvt_ip_addr: str = NodeNetworkParams.pvt_ip_addr
    bmc_user: str = NodeNetworkParams.bmc_user
    bmc_secret: str = NodeNetworkParams.bmc_secret

    _optional_param = [
        'public_ip_addr',
        'is_primary',
        'data_nw_netmask',
        'data_nw_gateway',
        'pvt_ip_addr'
    ]

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class ConfigureSetup(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureSetup

    validate_map = {"cluster": NetworkParamsValidation,
                    "node": NodeParamsValidation,
                    "storage_enclosure": StorageEnclosureParamsValidation}

    def _parse_params(self, input):
        params = {}
        for key in input:
            val = key.split(".")
            if val[-1] in [
                'ip', 'user', 'secret', 'ipaddr', 'iface', 'gateway', 'netmask'
            ]:
                params[f'{val[-2]}_{val[-1]}'] = input[key]
            else:
                params[val[-1]] = input[key]
        return params

    def _validate_params(self, input_type, content):
        params = self._parse_params(content)
        self.validate_map[input_type](**params)

    def _parse_input(self, input):
        for key in input:
            if input[key] and "," in input[key]:
                value = [f'\"{x.strip()}\"' for x in input[key].split(",")]
                value = ','.join(value)
                input[key] = f'[{value}]'
            else:
                if input[key]:
                    input[key] = f'\"{input[key]}\"'

    def _parse_pillar_key(self, key):
        pillar_key = deepcopy(key)
        return pillar_key.replace(".", "/")

    def run(self, path, number_of_nodes):

        if not Path(path).is_file():
            raise ValueError('config file is missing')

        config = configparser.ConfigParser()
        config.read(path)
        logger.info("Updating salt data :")
        content = {section: dict(config.items(section)) for section in config.sections()}  # noqa: E501
        logger.debug(f"params data {content}")

        input_type = None
        pillar_type = None
        count = int(number_of_nodes)
        for section in content:
            input_type = section
            pillar_type = section
            if 'srvnode' in section:
                input_type = 'node'
                pillar_type = f'cluster/{section}'
                count = count - 1
            self._validate_params(input_type, content[section])
            self._parse_input(content[section])

            for pillar_key in content[section]:
                key = f'{pillar_type}/{self._parse_pillar_key(pillar_key)}'
                run_subprocess_cmd([
                       "provisioner", "pillar_set",
                       key, f"{content[section][pillar_key]}"])

        if count > 0:
            raise ValueError(f"Node information for {count} node missing")

        logger.info("Pillar data updated Successfully.")
