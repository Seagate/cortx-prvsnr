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

from .. import inputs
from ..commands import (CommandParserFillerMixin, Check, SWUpdateDecisionMaker,
                        _apply_provisioner_config, _restart_salt_minions,
                        _update_component, _pre_yum_rollback)
from ..config import GroupChecks
from ..errors import (SWStackUpdateError, ClusterNotHealthyError,
                      SWUpdateError, SWUpdateFatalError,
                      ClusterMaintenanceDisableError, HAPostUpdateError)
from ..salt import StatesApplier, local_minion_id, YumRollbackManager
from ..salt_master import config_salt_master
from ..salt_minion import config_salt_minions
from ..vendor import attr


logger = logging.getLogger(__name__)


COMPONENTS_FOR_UPGRADE = frozenset({'motr',
                                    's3server',
                                    'hare',
                                    'ha.cortx-ha',
                                    'sspl',
                                    'uds',
                                    'csm'})


@attr.s(auto_attribs=True)
class SWUpgrade(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    @staticmethod
    def _ensure_upgrade_repos_configuration():
        logger.info("Ensure update repos are configured")
        StatesApplier.apply(['components.misc_pkgs.swupgrade.repo'],
                            local_minion_id())

        # logger.info("Check yum repos are good")
        # StatesApplier.apply(
        #     ['components.misc_pkgs.sw_update.repo.sanity_check'],
        #     local_minion_id()
        # )

    def run(self, targets):  # noqa: C901 FIXME
        # logic based on https://jts.seagate.com/browse/EOS-6611?focusedCommentId=1833451&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-1833451  # noqa: E501

        # TODO:
        #   - create a state instead
        #   - what about apt and other non-yum pkd managers
        #   (downgrade is another more generic option but it requires
        #    exploration of depednecies that are updated)
        # TODO IMPROVE minions might be stopped here in case of rollback,
        #      options: set up temp ssh config and rollback yum + minion config
        #      via ssh as a fallback
        rollback_ctx = None
        try:
            checker = Check()
            try:
                check_res = checker.run(GroupChecks.SWUPDATE_CHECKS.value)
            except Exception as e:
                logger.warning("During pre-flight checks error happened: "
                               f"{str(e)}")
            else:
                decision_maker = SWUpdateDecisionMaker()
                decision_maker.make_decision(check_result=check_res)

            self._ensure_upgrade_repos_configuration()

            with YumRollbackManager(
                            targets,
                            multiple_targets_ok=True,
                            pre_rollback_cb=_pre_yum_rollback) as rollback_ctx:
                try:
                    _update_component('provisioner', targets)

                    # re-apply provisioner configuration to ensure
                    # that updated pillar is taken into account
                    _apply_provisioner_config(targets)

                    config_salt_master()

                    minion_conf_changes = config_salt_minions()

                    for component in COMPONENTS_FOR_UPGRADE:
                        _update_component(component, targets)
                except Exception as exc:
                    raise SWStackUpdateError(exc) from exc

                # NOTE that should be the very final step of the logic
                #      since salt client will be restarted so the current
                #      process might start to wait itself
                if minion_conf_changes:
                    # TODO: Improve salt minion restart logic
                    # please refer to task EOS-14114.
                    try:
                        _restart_salt_minions()
                    except Exception:
                        logger.exception('failed to restart salt minions')

        except Exception as update_exc:
            # TODO TEST
            logger.exception('SW Upgrade failed')

            rollback_error = (
                None if rollback_ctx is None else rollback_ctx.rollback_error
            )
            final_error_t = SWUpdateError

            if rollback_error:
                # unrecoverable state: SW stack is in intermediate state,
                # no sense to start the cluster ??? verify TODO IMPROVE
                logger.error(
                    'Rollback failed: {}'.format(rollback_ctx.rollback_error))

                final_error_t = SWUpdateFatalError
            elif rollback_ctx is not None:
                if isinstance(
                    # cluster is stopped here
                    update_exc, (SWStackUpdateError,
                                 ClusterMaintenanceDisableError,
                                 HAPostUpdateError,
                                 ClusterNotHealthyError)):
                    # rollback provisioner related configuration
                    try:
                        config_salt_master()
                        config_salt_minions()
                        _apply_provisioner_config(targets)
                    except Exception as exc:
                        # unrecoverable state: SW stack is in intermediate
                        # state, no sense to start the cluster
                        logger.exception(
                                'Failed to restore SaltStack configuration')
                        rollback_error = exc
                        final_error_t = SWUpdateFatalError
                else:
                    # TODO TEST unit for that case
                    logger.warning(
                        'Unexpected case: update exc {!r}'.format(update_exc)
                    )

            # TODO IMPROVE
            raise final_error_t(update_exc,
                                rollback_error=rollback_error) from update_exc
