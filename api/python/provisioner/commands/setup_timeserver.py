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

"""Defines a module to setup time server on system"""

import logging
from typing import Type

from . import RunArgsEmpty
from ._basic import CommandParserFillerMixin
from ..errors import SaltError
from ..vendor import attr
from ..config import LOCAL_MINION
from ..pillar import (
    PillarKey,
    PillarResolver
)
from ..salt import function_run, StatesApplier
from .. import inputs, values

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SetupTimeServer(CommandParserFillerMixin):
    """Defines logic to setup time server on system"""

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsEmpty

    def run(self):
        logger.info("Setting up NTP time server")
        try:
            StatesApplier.apply(['components.system.chrony'], targets=LOCAL_MINION)
        except Exception as exc:
            logger.error("NTP configuration failed")
            raise SaltError(exc)
        logger.info("NTP setup successful")
