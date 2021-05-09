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

"""Defines sw_rollback module to perform CORTX software rollback"""

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
    YumRollbackManager,
    local_minion_id
)
from ..commands import _apply_provisioner_config
from ..salt_master import config_salt_master
from ..salt_minion import config_salt_minions
from .. import inputs, values

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSWRollback:
    """Specify usage of attributes required for rollback"""

    target_version: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "CORTX version to rollback "
                "in case yum rollback is not performed"
            }
        },
        default=None
    )
    targets: str = RunArgs.targets


@attr.s(auto_attribs=True)
class SWRollback(CommandParserFillerMixin):
    """Defines CORTX software rollback logic"""

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSWRollback

    @staticmethod
    def _rollback_component(component, targets):
        state_name = "{}.rollback".format(component)
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

        logger.info(f'Starting rollback process on {targets}')
        local_minion = local_minion_id()

        upgrade_path = PillarKey('upgrade')
        upgrade_dict = PillarResolver(local_minion).get([upgrade_path])
        upgrade_dict = upgrade_dict[local_minion][upgrade_path]

        try:
            if target_version:
                yum_snapshots = upgrade_dict.get('yum_snapshots', {})

                if not yum_snapshots:
                    raise ValueError(
                        'yum snapshots data not available for rollback'
                    )
                if target_version not in yum_snapshots:
                    raise ValueError(
                        f'yum snapshots not available for {target_version}'
                    )
                yum_txn_ids = yum_snapshots.get(target_version, {})
                logger.debug(
                    'YumRollbackManager will process yum_txn_ids: '
                    f'{yum_txn_ids}'
                )
                for target in yum_txn_ids:
                    txn_id = (yum_txn_ids[target])
                    if not txn_id or txn_id is values.MISSED:
                        raise BadPillarDataError(
                            f"yum txn id not available for {target}"
                        )
                    else:
                        YumRollbackManager()._yum_rollback(txn_id, target)

            # TODO Add provisioner to sw_list and
            # reconfigure provisioner through rollback state
            logger.debug(f'Restoring provisioner configuration on {targets}')
            config_salt_master()

            config_salt_minions()

            _apply_provisioner_config(targets)

            sw_list = upgrade_dict.get('sw_list', [])
            logger.debug(
                f'Components listed for rollback in upgrade/sw_list: {sw_list}'
            )
            if not sw_list:
                logger.warning('No components listed for rollback')

            for component in reversed(upgrade_dict['sw_list']):
                self._rollback_component(component, targets)

        except Exception as exc:
            raise SWRollbackError(exc) from exc

        logger.info('Rollback completed')
