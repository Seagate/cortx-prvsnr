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

from . import (CommandParserFillerMixin, _ensure_update_repos_configuration,
               _pre_yum_rollback, _update_component, _apply_provisioner_config
               )
from .check import Check

# TODO consider to use RunArgsUpdate and support dry-run
from .. import inputs
from ..config import LOCAL_MINION
from ..errors import (ClusterMaintenanceEnableError, SWStackUpdateError,
                      ClusterMaintenanceDisableError, HAPostUpdateError,
                      ClusterNotHealthyError, SWUpdateError, SWUpdateFatalError
                      )
from ..hare import (ensure_cluster_is_healthy, consul_export,
                    cluster_maintenance_disable, apply_ha_post_update,
                    cluster_maintenance_enable
                    )
from ..salt import YumRollbackManager, cmd_run as salt_cmd_run

from ..salt_master import config_salt_master, ensure_salt_master_is_running
from ..salt_minion import config_salt_minions
from ..vendor import attr

logger = logging.getLogger(__name__)


def _consul_export(stage):
    # TODO make that configurable to turn off if not needed
    logger.info(f'Exporting consul [{stage}]')
    consul_export(fn_suffix=stage)


def _restart_salt_minions():
    logger.info("Restarting salt minions")
    salt_cmd_run(
        'systemctl restart salt-minion', background=True
    )


# TODO consider to use RunArgsUpdate and support dry-run
@attr.s(auto_attribs=True)
class SWUpdate(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, targets):  # noqa: C901 FIXME
        # logic based on https://jts.seagate.com/browse/EOS-6611?focusedCommentId=1833451&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-1833451  # noqa: E501

        checker = Check()
        check_res = checker.run(targets=LOCAL_MINION)
        if check_res.is_failed:
            failed = "; ".join(str(check) for check in check_res.get_failed())
            raise SWUpdateError("Some pre-flight checks are failed: "
                                f"{failed}")

        # TODO:
        #   - create a state instead
        #   - what about apt and other non-yum pkd managers
        #   (downgrade is another more generic option but it requires
        #    exploration of depednecies that are updated)
        # TODO IMPROVE minions might be stopped here in case of rollback,
        #      options: set up temp ssh config and rollback yum + minion config
        #      via ssh as a fallback
        rollback_ctx = None
        minion_conf_changes = None
        try:
            ensure_cluster_is_healthy()

            _ensure_update_repos_configuration(targets)

            _consul_export('update-pre')

            with YumRollbackManager(
                targets,
                multiple_targets_ok=True,
                pre_rollback_cb=_pre_yum_rollback
            ) as rollback_ctx:
                # enable "smart maintenance" mode
                try:
                    cluster_maintenance_enable()
                except Exception as exc:
                    raise ClusterMaintenanceEnableError(exc) from exc

                # update SW stack packages and configuration
                try:
                    _update_component('provisioner', targets)

                    config_salt_master()

                    minion_conf_changes = config_salt_minions()

                    for component in (
                        'motr',
                        's3server',
                        'hare',
                        'ha.cortx-ha',
                        'sspl',
                        'csm',
                        'uds'
                    ):
                        _update_component(component, targets)
                except Exception as exc:
                    raise SWStackUpdateError(exc) from exc

                # SW stack now in "updated" state
                # disable "smart maintenance" mode
                try:
                    cluster_maintenance_disable()
                except Exception as exc:
                    raise ClusterMaintenanceDisableError(exc) from exc

                _consul_export('update-pre-ha-update')

                # call Hare to update cluster configuration
                try:
                    apply_ha_post_update(targets)
                except Exception as exc:
                    raise HAPostUpdateError(exc) from exc

                _consul_export('update-post-ha-update')

                try:
                    ensure_cluster_is_healthy()
                except Exception as exc:
                    raise ClusterNotHealthyError(exc) from exc

                _consul_export('update-post')

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
            logger.exception('SW Update failed')

            rollback_error = (
                None if rollback_ctx is None else rollback_ctx.rollback_error
            )
            final_error_t = SWUpdateError

            if rollback_error:
                # unrecoverable state: SW stack is in intermediate state,
                # no sense to start the cluster ??? verify TODO IMPROVE
                logger.error(
                    'Rollback failed: {}'
                    .format(rollback_ctx.rollback_error)
                )
                final_error_t = SWUpdateFatalError
            elif rollback_ctx is not None:
                # yum packages are in initial state here

                if isinstance(update_exc, ClusterMaintenanceEnableError):
                    # failed to activate maintenance, cluster will likely
                    # fail to start - fail gracefully:  disable
                    # maintenance in the background
                    cluster_maintenance_disable(background=True)
                elif isinstance(
                    # cluster is stopped here
                    update_exc,
                    (
                        SWStackUpdateError,
                        ClusterMaintenanceDisableError,
                        HAPostUpdateError,
                        ClusterNotHealthyError
                    )
                ):
                    # rollback provisioner related configuration
                    try:
                        ensure_salt_master_is_running()

                        config_salt_master()

                        config_salt_minions()

                        _apply_provisioner_config(targets)

                    except Exception as exc:
                        # unrecoverable state: SW stack is in intermediate
                        # state, no sense to start the cluster
                        logger.exception(
                            'Failed to restore SaltStack configuration'
                        )
                        rollback_error = exc
                        final_error_t = SWUpdateFatalError
                    else:
                        # SW stack now in "initial" state
                        try:
                            cluster_maintenance_disable()

                            _consul_export('rollback-pre-ha-update')

                            apply_ha_post_update(targets)

                            _consul_export('rollback-post-ha-update')

                            ensure_cluster_is_healthy()

                            _consul_export('rollback-post')
                        except Exception as exc:
                            # unrecoverable state: SW stack is in initial
                            # state but cluster failed to start
                            logger.exception(
                                'Failed to recover cluster after rollback'
                            )
                            rollback_error = exc
                            final_error_t = SWUpdateFatalError

                        # update failed but node is in initial state
                        # and looks functional
                else:
                    # TODO TEST unit for that case
                    logger.warning(
                        'Unexpected case: update exc {!r}'.format(update_exc)
                    )

            # TODO IMPROVE
            raise final_error_t(
                update_exc, rollback_error=rollback_error
            ) from update_exc
