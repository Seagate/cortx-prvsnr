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

from provisioner import ALL_MINIONS

from .set_swupgrade_repo import SetSWUpgradeRepo
from .. import inputs

logger = logging.getLogger(__name__)


class RemoveSWUpgradeRepo(SetSWUpgradeRepo):

    input_type: Type[inputs.SWUpgradeRemoveRepo] = inputs.SWUpgradeRemoveRepo

    def run(self, *args, targets=ALL_MINIONS, dry_run=False,
            local=False, **kwargs):
        # static validation
        if len(args) == 1 and isinstance(args[0], self.input_type):
            params = args[0]
        else:
            params = self.input_type.from_args(*args, **kwargs)

        if dry_run:
            return

        if not self._does_repo_exist(f'sw_upgrade_*_{params.release}'):
            logger.warning(
                f"SW upgrade repo of release '{params.release}' was not found"
            )
            return

        logger.info("Start removing SW upgrade repo of release "
                    f"'{params.release}'")

        self._apply(params, targets=targets, local=local)

        logger.info(f"SW upgrade repo of release '{params.release}' "
                    f"was successfully removed")
