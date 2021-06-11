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

# Provisioner CLI to reset machine id on all nodes
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
class ResetMachineId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsMachineIdAttrs
    description = "API to reset machine id on all nodes"

    @staticmethod
    def run(**kwargs):

        machine_id_reset_states = []
        if 'force' in kwargs and kwargs['force']:
            logger.debug("machine_id on all nodes shall be forcefully reset.")
            machine_id_reset_states.append(
                "components.provisioner.config.machine_id.force_reset")
        else:
            logger.debug("machine_id on all nodes shall be reset.")
            machine_id_reset_states.append(
                "components.provisioner.config.machine_id.reset")

        logger.debug("Refresh grains on all nodes post machine_id reset.")
        machine_id_reset_states.append(
            "components.provisioner.config.machine_id.refresh_grains")

        logger.info("Resetting machine_id on all nodes.")
        StatesApplier.apply(machine_id_reset_states)
        logger.info("SUCCESS: machine_id is reset.")
