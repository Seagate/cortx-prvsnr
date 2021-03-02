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

# Provisioner CLI to refresh machine id
import logging
from typing import Type

from ..salt import StatesApplier
from .. import (
    inputs
)
from ..vendor import attr

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsMachineIdAttrs:
    force: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Forcefully update machine_id",
            }
        },
        default=False
    )


@attr.s(auto_attribs=True)
class RefreshMachineId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsMachineIdAttrs
    description = "API to refresh machine id on all nodes"

    @staticmethod
    def run(**kwargs):

        if kwargs['force']:
            logger.info("Forcefully refresh machine id on all nodes")
            state = "components.provisioner.config.machine_id.force_refresh"
        else:
            logger.info("Refreshing machine id on all nodes")
            state = "components.provisioner.config.machine_id.refresh_machine_id"  # noqa: E501

        StatesApplier.apply([state])

        logger.info("refresh grains on all nodes")
        StatesApplier.apply(
            ["components.provisioner.config.machine_id.refresh_grains"]
        )
        logger.info("Machine id refreshed successfully.")
