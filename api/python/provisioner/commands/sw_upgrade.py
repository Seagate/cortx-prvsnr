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
import json

from .. import inputs, values
from ..commands import (CommandParserFillerMixin, Check, SWUpdateDecisionMaker,
                        _apply_provisioner_config, _restart_salt_minions,
                        _update_component, _pre_yum_rollback, GetReleaseVersion
                        )
from ..config import GroupChecks, ReleaseInfo
from ..errors import SWStackUpdateError, SWUpdateError, SWUpdateFatalError
from ..pillar import PillarKey, PillarResolver, PillarUpdater
from ..salt import (StatesApplier, local_minion_id, YumRollbackManager,
                    get_last_txn_ids
                    )
from ..salt_master import config_salt_master
from ..salt_minion import config_salt_minions
from ..vendor import attr


logger = logging.getLogger(__name__)


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

    @staticmethod
    def _handle_error(update_exc, rollback_ctx, targets):
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
            if isinstance(update_exc, (SWStackUpdateError,)):
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

    @staticmethod
    def _get_pillar(pillar_key_path: str, targets: str) -> dict:
        """
        Get Pillar value
        Parameters
        ----------
        pillar_key_path: str
            Pillar key path

        targets: str
            targets to retrieve the pillar values

        Returns
        -------
        dict
            dictionary with pillar values for each requested target

        """
        pillar_path = PillarKey(pillar_key_path)
        pillar = PillarResolver(targets).get([pillar_path])

        _res = dict()
        for target, _pillar in pillar.items():
            if (not _pillar[pillar_path]
                    or _pillar[pillar_path] is values.MISSED):
                raise ValueError("value is not specified for "
                                 f"'{pillar_path}' and target '{target}'")
            else:
                _res[target] = _pillar[pillar_path]

        return _res

    def run(self, targets):  # noqa
        # TODO:
        #   - create a state instead
        #   - what about apt and other non-yum pkd managers
        #   (downgrade is another more generic option but it requires
        #    exploration of depednecies that are updated)
        # TODO IMPROVE minions might be stopped here in case of rollback,
        #      options: set up temp ssh config and rollback yum + minion config
        #      via ssh as a fallback
        rollback_ctx = None

        checker = Check()
        try:
            check_res = checker.run(GroupChecks.SWUPDATE_CHECKS.value)
        except Exception as e:
            logger.warning("During pre-flight checks error happened: "
                           f"{str(e)}")
        else:
            decision_maker = SWUpdateDecisionMaker()
            decision_maker.make_decision(check_result=check_res)

        try:
            self._ensure_upgrade_repos_configuration()

            local_minion = local_minion_id()

            version_resolver = GetReleaseVersion()
            release_info = version_resolver.run(targets=local_minion)  # str
            release_info = json.loads(release_info)
            cortx_version = (f"{release_info[ReleaseInfo.VERSION.value]}-"
                             f"{release_info[ReleaseInfo.BUILD.value]}")

            upgrade_data = self._get_pillar('upgrade', local_minion)

            # TODO: we need to compare targets in yum_snapshots and targets
            #  from parsed income parameter
            #  for example:
            #  yum_snapshots:
            #    - <cortx_version>:
            #       - srvnode-1: <id>
            # and input targets = "*" for cluster with >= 2 nodes
            # so possible scenario:
            # provisioner sw_upgrade --targets="srvnode-1"
            # provisioner sw_upgrade --targets="*"
            txn_ids_dict = get_last_txn_ids(targets=targets,
                                            multiple_targets_ok=True)

            pillar_updater = PillarUpdater(targets)

            yum_snapshot_path = PillarKey(
                                    f"upgrade/yum_snapshots/{cortx_version}")

            pi_group = inputs.PillarInputBase.from_args(
                                                keypath=yum_snapshot_path,
                                                value=txn_ids_dict)

            pillar_updater.update(pi_group)
            pillar_updater.apply()

            sw_list = upgrade_data[local_minion].get("sw_list", None)

            if not sw_list:
                raise ValueError("upgrade/sw_list data is missed")

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

                    for component in sw_list:
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

            self._handle_error(update_exc, rollback_ctx, targets)
