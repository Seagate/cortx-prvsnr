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
# Module with all network-related validations


import logging

from ...inputs import (
    NetworkParams
)
from ...values import UNCHANGED
from ...vendor import attr

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class NetworkParamsValidator:
    cluster_ip: str = NetworkParams.cluster_ip
    mgmt_vip: str = NetworkParams.mgmt_vip
    _optional_param = [
        'cluster_ip',
        'mgmt_vip'
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
