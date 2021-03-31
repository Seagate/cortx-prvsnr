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
# Module with all node-related validations


import logging
from typing import List

from ..grains_get import GrainsGet
from ...inputs import (
    NodeParams
)
from ...values import UNCHANGED
from ...vendor import attr
from ...salt import local_minion_id

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class NodeParamsValidator:
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

    def __attrs_post_init__(self):    # noqa: D105
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
        if (
            not 'physical' in GrainsGet().run(
                'virtual',
                targets=local_minion_id()
            )[local_minion_id()]['virtual']
        ):
            self._optional_param.extend([
                'bmc_user',
                'bmc_secret'
            ])

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
