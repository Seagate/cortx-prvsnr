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
from typing import Type

from ..salt import (
    StatesApplier,
    cmd_run
)
from .. import (
    inputs,
    utils,
    config
)
from ..vendor import attr

from . import (
    CommandParserFillerMixin,
    PillarSet
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsServiceUser:
    user: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Service user name default: cortxub",
            }
        },
        default='cortxub'
    )


@attr.s(auto_attribs=True)
class CreateServiceUser(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsServiceUser
    description = "API to create service user"

    @staticmethod
    def run(**kwargs):

        logger.info("Generating a password for the service user")
        user = kwargs.pop('user')
        if user:
            logger.info(f"Updating service user name {user}")
            PillarSet().run(
                'system/service-user/name',
                f'{user}'
            )

        service_user_password = utils.generate_random_secret()
        PillarSet().run(
                'system/service-user/password',
                f'{service_user_password}'
        )

        logger.info("Creating service user.")

        StatesApplier.apply(["components.system.config.service_user"])
        logger.info("SUCCESS: service user is created.")
