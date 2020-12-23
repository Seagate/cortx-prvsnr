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
import configparser
from enum import Enum
from typing import Type, List
from copy import deepcopy
from pathlib import Path

from ..inputs import (
    NetworkParams, ReleaseParams, StorageEnclosureParams,
    NodeNetworkParams, ServerDefaultParams
)
from .. import inputs
from ..vendor import attr

from ..utils import run_subprocess_cmd

from ..values import UNCHANGED
from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


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
    primary_mc_ip: str = StorageEnclosureParams.primary_mc_ip
    secondary_mc_ip: str = StorageEnclosureParams.secondary_mc_ip
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
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class NodeParamsValidation:
    hostname: str = NodeNetworkParams.hostname
    is_primary: str = NodeNetworkParams.is_primary
    data_nw_iface: List = NodeNetworkParams.data_nw_iface
    data_nw_public_ip_addr: str = NodeNetworkParams.data_nw_public_ip_addr
    data_nw_netmask: str = NodeNetworkParams.data_nw_netmask
    data_nw_gateway: str = NodeNetworkParams.data_nw_gateway
    mgmt_nw_iface: List = NodeNetworkParams.mgmt_nw_iface
    mgmt_nw_public_ip_addr: str = NodeNetworkParams.mgmt_nw_public_ip_addr
    mgmt_nw_netmask: str = NodeNetworkParams.mgmt_nw_netmask
    mgmt_nw_gateway: str = NodeNetworkParams.mgmt_nw_gateway
    pvt_ip_addr: str = NodeNetworkParams.pvt_ip_addr
    bmc_user: str = NodeNetworkParams.bmc_user
    bmc_secret: str = NodeNetworkParams.bmc_secret

    _optional_param = [
        'data_nw_public_ip_addr',
        'is_primary',
        'data_nw_netmask',
        'data_nw_gateway',
        'pvt_ip_addr',
        'mgmt_nw_iface',
        'mgmt_nw_public_ip_addr',
        'mgmt_nw_netmask',
        'mgmt_nw_gateway'
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
class ServerDefaultParamsValidation:
    search_domains: str = ServerDefaultParams.search_domains
    dns_servers: str = ServerDefaultParams.dns_servers
    # TO DO: Include Network, Storage params

    _optional_param = []

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            raise ValueError(f"Mandatory param missing {missing_params}")
