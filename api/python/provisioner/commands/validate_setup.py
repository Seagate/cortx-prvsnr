#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from typing import List

from ..inputs import (
    NetworkParams, ReleaseParams, StorageEnclosureParams,
    NodeNetworkParams, NodeParams
)
from ..vendor import attr

from ..values import UNCHANGED

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
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
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
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class StorageEnclosureParamsValidation:
    type: str = StorageEnclosureParams.type
    controller_primary_mc_ip: str = (
                        StorageEnclosureParams.controller_primary_mc_ip)
    controller_secondary_mc_ip: str = (
                        StorageEnclosureParams.controller_secondary_mc_ip)
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
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class StorageNodeParamsValidation:
    hostname: str = StorageEnclosureParams.hostname
    _optional_param = []

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class NodeNetworkParamsValidation:
    search_domains: str = NetworkParams.search_domains
    dns_servers: str = NetworkParams.dns_servers
    cluster_id: str = NodeNetworkParams.cluster_id
    bmc_user: str = NodeNetworkParams.bmc_user
    bmc_secret: str = NodeNetworkParams.bmc_secret
    network_data_interfaces: str = NodeNetworkParams.network_data_interfaces
    network_data_netmask: str = NodeNetworkParams.network_data_netmask
    network_data_gateway: str = NodeNetworkParams.network_data_gateway
    network_mgmt_interfaces: List = NodeNetworkParams.network_mgmt_interfaces
    network_mgmt_netmask: str = NodeNetworkParams.network_mgmt_netmask
    network_mgmt_gateway: str = NodeNetworkParams.network_mgmt_gateway
    pvt_ip_addr: str = NodeNetworkParams.pvt_ip_addr
    storage_metadata_device: str = StorageEnclosureParams.storage_metadata_device
    storage_data_devices: str = StorageEnclosureParams.storage_data_devices


    _optional_param = [
        'search_domains',
        'dns_servers',
        'cluster_id',
        'network_data_netmask',
        'network_data_gateway',
        'pvt_ip_addr',
        'network_mgmt_interfaces',
        'network_mgmt_netmask',
        'network_mgmt_gateway'
    ]

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
            raise ValueError(f"Mandatory param missing {missing_params}")


@attr.s(auto_attribs=True)
class NodeParamsValidation:
    hostname: str = NodeParams.hostname
    is_primary: str = NodeParams.is_primary
    roles: str = NodeParams.roles
    bmc_ip: str = NodeParams.bmc_ip
    cluster_id: str = NodeNetworkParams.cluster_id
    bmc_user: str = NodeNetworkParams.bmc_user
    bmc_secret: str = NodeNetworkParams.bmc_secret
    network_data_public_ip_addr: str = NodeNetworkParams.network_data_public_ip_addr
    network_mgmt_public_ip_addr: str = NodeNetworkParams.network_mgmt_public_ip_addr


    _optional_param = [
        'is_primary',
        'bmc_user',
        'bmc_ip',
        'bmc_secret',
        'cluster_id',
        'network_data_public_ip_addr',
        'network_mgmt_public_ip_addr'
    ]

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        missing_params = []
        for param, value in params.items():
            if value == UNCHANGED and param not in self._optional_param:
                missing_params.append(param)
        if len(missing_params) > 0:
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
            raise ValueError(f"Mandatory param missing {missing_params}")
