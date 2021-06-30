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
from provisioner.api_spec import param_spec
from provisioner.inputs import ParamDictItemInputBase
from provisioner.lock import api_lock
from provisioner.pillar import (PillarKey,
                                PillarUpdater,
                                PillarResolver)
from provisioner.salt import local_minion_id
from provisioner.vendor import attr

from .set_swupgrade_repo import SetSWUpgradeRepo
from .. import inputs

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RemoveSWUpgradeItems(ParamDictItemInputBase):

    _param_di = param_spec['swupgrade/repo']
    _values = None
    params: inputs.SWUpgradeRemoveRepo = attr.ib(init=True)
    targets: str = attr.ib(default=ALL_MINIONS)

    @property
    def pillar_key(self):
        return ''  # keep it empty since we use the root path from _param_di

    @property
    def pillar_value(self):
        pillar_path = 'release/upgrade/repos'
        pillars = PillarResolver(self.targets).get(
            [PillarKey(pillar_path)],
            fail_on_undefined=True
        )

        repos = pillars[local_minion_id()][PillarKey(pillar_path)]

        deleted = repos.pop(self.params.release)

        logger.debug(f"Delete block of pillar values: "
                     f"'{{ {self.params.release}: {deleted} }}'")

        return repos


class RemoveSWUpgradeRepo(SetSWUpgradeRepo):

    input_type: Type[inputs.SWUpgradeRemoveRepo] = inputs.SWUpgradeRemoveRepo

    @staticmethod
    def _clean_up_pillars(params: inputs.SWUpgradeRemoveRepo,
                          targets=ALL_MINIONS, local=False):
        """
        Clean up unused and unnecessary pillar values for SW upgrade

        Parameters
        ----------
        params: inputs.SWUpgradeRemoveRepo
            input parameters for remove command
        targets: str
            List of targets where pillar values are suggested for removal.

        Returns
        -------
        None

        """

        pillar_updater = PillarUpdater(targets, local=local)

        update_values = RemoveSWUpgradeItems(targets=targets, params=params)
        pillar_updater.update(update_values)
        pillar_updater.apply()

    @api_lock
    def run(self, *args, targets=ALL_MINIONS, dry_run=False,
            local=False, **kwargs):
        """
        Base command for SW upgrade repository removal.

        Parameters
        ----------
        targets: str
            List of targets where pillar values are suggested for removal.
        dry_run: bool
            Parse parameters and doesn't remove repositories
        local: bool
            Specifies locality of SW upgrade Pillar values

        Returns
        -------
        None

        """
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
        logger.info("Yum repo files are successfully removed. "
                    "Start pillars cleaning up procedure...")

        self._clean_up_pillars(params, targets)

        logger.info(f"SW upgrade repo of release '{params.release}' "
                    f"was successfully removed")
