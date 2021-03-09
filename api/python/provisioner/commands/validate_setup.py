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
    ClusterParams,
    StorageParams,
    NodeParams
)
from ..vendor import attr
from ..config import (
    NODE_DEFAULT,
    STORAGE_DEFAULT
)

from ..values import UNCHANGED

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ValidateSetup:

    def _parse_nodes(self, content):
        """
        Parses the content of nodes.

        The node names are parsed based on config-sections.

        """
        section_list = []
        output = {}
        for section in content:
            section_list.append(f"{section}")

        # Gives section names of only nodes : srvnode[1-12]
        servers = [srv for srv in sorted(section_list) if "srvnode" in srv and "default" not in srv]

        # Gives section names of only nodes : storage-enclosure[1-12]
        enclosures = [enc for enc in sorted(section_list) if "storage" in enc and "default" not in enc]

        output["section_list"] = section_list
        output["server_default"] = f'{NODE_DEFAULT}'
        output["storage_default"] = f'{STORAGE_DEFAULT}'
        output["server_list"] = servers
        output["storage_list"] = enclosures

        return output

# TODO: validate node count method
# will be merged here as part of EOS-16553


@attr.s(auto_attribs=True)
class ClusterParamsValidation:
    cluster_ip: str = ClusterParams.cluster_ip
    mgmt_vip: str = ClusterParams.mgmt_vip
    cluster_id: str = ClusterParams.cluster_id
    _optional_param = [
        'cluster_ip',
        'mgmt_vip',
        'cluster_id'
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
class StorageParamsValidation:
    type: str = StorageParams.type
    primary_ip: str = StorageParams.controller_primary_ip
    secondary_ip: str = StorageParams.controller_secondary_ip
    controller_user: str = StorageParams.controller_user
    controller_secret: str = StorageParams.controller_secret
    controller_type: str = StorageParams.controller_type
    _optional_param = [
        'primary_ip',
        'secondary_ip',
        'controller_user',
        'controller_secret',
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
class NodeParamsValidation:
    hostname: str = NodeParams.hostname
    is_primary: str = NodeParams.is_primary
    roles: str = NodeParams.roles
    bmc_ip: str = NodeParams.bmc_ip
    bmc_user: str = NodeParams.bmc_user
    bmc_secret: str = NodeParams.bmc_secret
    data_public_interfaces: List = NodeParams.data_public_interfaces
    data_private_interfaces: List = NodeParams.data_private_interfaces
    data_netmask: str = NodeParams.data_netmask
    data_gateway: str = NodeParams.data_gateway
    mgmt_interfaces: List = NodeParams.mgmt_interfaces
    mgmt_netmask: str = NodeParams.mgmt_netmask
    mgmt_gateway: str = NodeParams.mgmt_gateway
    data_private_ip: str = NodeParams.data_private_ip
    search_domains: str = NodeParams.search_domains
    dns_servers: str = NodeParams.dns_servers
    data_public_ip: str = NodeParams.data_public_ip
    mgmt_public_ip: str = NodeParams.mgmt_public_ip
    metadata_devices: List = StorageParams.storage_metadata_devices
    data_devices: List = StorageParams.storage_data_devices

    _optional_param = [
        'is_primary',
        'roles',
        'bmc_ip',
        'search_domains',
        'dns_servers',
        'data_netmask',
        'data_gateway',
        'mgmt_netmask',
        'mgmt_gateway',
        'data_public_ip',
        'mgmt_public_ip',
        'data_public_interfaces',
        'metadata_devices',
        'data_devices'
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
