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

from ._basic import RunArgs, CommandParserFillerMixin
from ..vendor import attr
from ..config import ALL_MINIONS
from ..errors import (
    BadPillarDataError,
    SWRollbackError,
)
from ..pillar import (
    PillarKey,
    PillarResolver
)
from ..salt import (
    StatesApplier,
    cmd_run as salt_cmd_run,
    local_minion_id
)
from ..commands import _apply_provisioner_config
from ..salt_master import config_salt_master
from ..salt_minion import config_salt_minions
from .. import inputs, values

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSWRollback:
    target_version: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Cortex version to rollback "
                "in case yum rollback is not performed"
            }
        },
        default=None
    )
    targets: str = RunArgs.targets


@attr.s(auto_attribs=True)
class SWRollback(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSWRollback

    @staticmethod
    def _rollback_component(component, targets):
        state_name = "components.{}.rollback".format(component)
        try:
            logger.info(
                "Restoring {} configuration on {}".format(component, targets)
            )
            StatesApplier.apply([state_name], targets)
        except Exception:
            logger.exception(
                "Failed to restore {} on {}".format(component, targets)
            )
            raise

    def run(self, target_version=None, targets=ALL_MINIONS):

        local_minion = local_minion_id()

        upgrade_path = PillarKey('upgrade')
        upgrade_pillar = PillarResolver(local_minion).get([upgrade_path])
        upgrade_pillar = upgrade_pillar[local_minion][upgrade_path]

        try:
            if target_version:
                yum_snapshots = upgrade_pillar['yum_snapshots']
                if target_version not in yum_snapshots:
                    raise ValueError(
                        f'yum snapshots not available for {target_version}'
                    )
                else:
                    for target in yum_snapshots[target_version].keys():
                        txn_id = (
                            yum_snapshots[target_version][target]
                        )
                        if not txn_id or txn_id is values.MISSED:
                            raise BadPillarDataError(
                                f"yum txn id not available for {target}"
                            )
                        else:
                            logger.info(
                                f"Starting yum rollback on target {target}"
                            )
                            salt_cmd_run(
                                f"yum history rollback -y {txn_id}",
                                targets=target
                            )
                            logger.info(
                                f"Yum rollback on target {target} is completed"
                            )
            logger.info('Restoring cortex components configuration')

            # TODO
            # reconfigure provisioner through rollback state
            config_salt_master()

            config_salt_minions()

            _apply_provisioner_config(targets)

            for component in reversed(upgrade_pillar['sw_list']):
                self._rollback_component(component, targets)

            logger.info(
                'Configurations restored successfully'
            )
        except Exception as exc:
            raise SWRollbackError(exc) from exc
        else:
            logger.info(
                'Rollback completed'
            )
