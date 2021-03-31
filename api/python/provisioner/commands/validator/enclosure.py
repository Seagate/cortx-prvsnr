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
# Module with all storage-enclosure-related validations


import logging

from ...inputs import (
    StorageEnclosureParams
)
from ...values import UNCHANGED
from ...vendor import attr

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class StorageEnclosureParamsValidator:
    type: str = StorageEnclosureParams.type
    primary_ip: str = StorageEnclosureParams.primary_ip
    secondary_ip: str = StorageEnclosureParams.secondary_ip
    controller_user: str = StorageEnclosureParams.controller_user
    controller_secret: str = StorageEnclosureParams.controller_secret
    controller_type: str = StorageEnclosureParams.controller_type
    _optional_param = [
        'controller_type'
    ]

    def __attrs_post_init__(self):    # noqa: D105
        params = attr.asdict(self)
        # FIXME why we allow any params for the following types?
        types = ['JBOD', 'virtual', 'RBOD', 'other']
        if params['type'] in types:
            return
        missing_params = []
        for param, value in params.items():
            if (
                value == UNCHANGED and
                param not in self._optional_param and
                params['type'] == 'RBOD'
            ):
                missing_params.append(param)

        if len(missing_params) > 0:
            logger.error(
                f"{missing_params} cannot be left empty or blank.. "
                "These are mandatory to configure the setup."
            )
            raise ValueError(f"Mandatory param missing {missing_params}")
