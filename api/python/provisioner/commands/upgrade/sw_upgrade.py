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
from typing import Type, List

from provisioner import __version__
from provisioner.vendor import attr
from provisioner.attr_gen import attr_ib
from provisioner import inputs
from provisioner.commands import (
    CommandParserFillerMixin,
    # Check,
    # SWUpdateDecisionMaker,
    # _apply_provisioner_config,
    # _restart_salt_minions,
    GetReleaseVersion,
    PillarSet
)
from provisioner.config import ALL_MINIONS  # , GroupChecks
from provisioner.errors import SWUpdateError
from provisioner.salt import (
    StatesApplier,
    local_minion_id,
    get_last_txn_ids,
    cmd_run,
    list_minions
)
# from provisioner.salt_master import config_salt_master
# from provisioner.salt_minion import config_salt_minions

from provisioner.cortx_ha import (
    cluster_stop,
    cluster_start,
    check_cluster_health_status
)


from .sw_upgrade_node import SWUpgradeNode


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSWUpgrade:
    # Note. targets are not considered, all the cluster always
    offline: bool = attr_ib(
        cli_spec='upgrade/orchestrator/offline', default=False
    )
    noprepare: bool = attr_ib(
        cli_spec='upgrade/orchestrator/noprepare', default=False
    )


@attr.s(auto_attribs=True)
class SWUpgrade(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSWUpgrade

    @staticmethod
    def _ensure_upgrade_repos_configuration():
        StatesApplier.apply(['repos.upgrade'], local_minion_id())

        # TODO FIXME review and activate
        # logger.info("Check yum repos are good")
        # StatesApplier.apply(
        #     ['components.misc_pkgs.sw_update.repo.sanity_check'],
        #     local_minion_id()
        # )

    def validate(self):
        logger.info('SW Upgrade Validation')
        check_cluster_health_status()

        logger.info("Ensure update repos are configured")
        self._ensure_upgrade_repos_configuration()

        # TODO FIXME verify and activate
        # checker = Check()
        # try:
        #     check_res = checker.run(GroupChecks.SWUPGRADE_CHECKS.value)
        # except Exception as e:
        #     logger.warning("During pre-flight checks error happened: "
        #                    f"{str(e)}")
        # else:
        #     decision_maker = SWUpdateDecisionMaker()
        #     decision_maker.make_decision(check_result=check_res)

        # TODO FIXME ??? check ISO is compatible with all the nodes
        #      (even if it was checked during ISO setup)

    def backup(self, cortx_version):
        logger.info('SW Upgrade Backup (cluster level)')
        # Note. not documented in the design, mostly legacy but useful logic

        logger.info('Storing current state of the yum history')
        txn_ids_dict = get_last_txn_ids(
            targets=ALL_MINIONS, multiple_targets_ok=True
        )
        logger.debug("Current list of yum txn ids: {txn_ids_dict}")

        PillarSet().run(
            f"upgrade/yum_snapshots/{cortx_version}",
            txn_ids_dict
        )

    def self_upgrade(self):
        # here we can use python API (SWUpgradeNode) since
        # old provisioner version would be called anyway
        logger.info('Upgrading Provisioner on all the nodes')
        SWUpgradeNode().run(sw=['provisioner'], no_events=True)

        # support for a separate orchestrator module
        # todo: can be a python API call if no changes for provisioner
        # logger.info('Upgrading Orchestrator on all the nodes')
        # cmd_run('provisioner sw_upgrade_node --sw orchestrator')

    def delegate(self, offline=False):
        logger.info(
            "SW Upgrade: delegating remaing phases"
            " to upgraded orchestrator logic"
        )
        return cmd_run(
            "provisioner sw_upgrade --noprepare"
            f"{' --offline' if offline else ''}"
        )

    def plan_upgrade(self, offline=False):
        res = []

        logger.info("SW Upgrade Plan Build")
        if not offline:
            raise NotImplementedError("Not considered for the current moment")
        else:
            # trivial - all nodes in parallel
            res = [list_minions()]

        logger.info(f"Upgrade plan is: '{res}'")
        return res

    def stop_cluster(self):
        # logger.info("Moving the Cortx cluster into standby mode")
        # FIXME cluster_standby()
        logger.info("Stopping the Cortx cluster")
        cluster_stop()

    def upgrade_cluster(self, planned_node_groups: List[List[str]]):
        logger.info("Fire pre-upgrade event (cluster level)")
        # FIXME pre-upgrade calls
        # Assumptions:
        #   resources cleanup and final cluster stop of should
        #   happen as part of pre-uprgade HA call

        for group in planned_node_groups:
            logger.info(f"Upgrading nodes: '{group}'")
            # XXX ??? provisioner (orchestrator) have been already
            #         upgraded, do we need to upgrade them here?
            SWUpgradeNode().run(targets=group)

        logger.info("Fire post-upgrade event (cluster level)")
        # FIXME post-upgrade calls

    def start_cluster(self):
        logger.info("Starting the Cortx cluster")
        cluster_start()

    def prepare(self, cortx_version):
        self.validate()

        self.backup(cortx_version)

        self.self_upgrade()

    def upgrade(self, offline=False):
        # TODO: can skip that if no changes for Orchestrator
        ret = cmd_run('provisioner --version')
        new_prvsnr_version = next(iter(ret.values()))
        # Note. assumption: case new version < old version is validated
        #       as part of validate stage
        if new_prvsnr_version != __version__:
            return self.delegate(offline=offline)
        else:
            logger.info(
                "SW Upgrade upgraded logic is the same as the"
                " current one, proceeding without delegation"
            )

        # noprepare is True or new logic is the same
        planned_node_groups = self.plan_upgrade(offline=offline)

        self.stop_cluster()

        self.upgrade_cluster(planned_node_groups)

        self.start_cluster()

        # TODO make the folllowing a part of migration
        #      routine on a node level
        # # re-apply provisioner configuration to ensure
        # # that updated pillar is taken into account
        # _apply_provisioner_config(targets)
        # config_salt_master()
        # minion_conf_changes = config_salt_minions()
        # ...
        # TODO make the folllowing a part of migration
        #      routine on a node level
        # # NOTE that should be the very final step of the logic
        # #      since salt client will be restarted so the current
        # #      process might start to wait itself
        # if minion_conf_changes:
        #     # TODO: Improve salt minion restart logic
        #     # please refer to task EOS-14114.
        #     try:
        #         _restart_salt_minions()
        #     except Exception:
        #         logger.exception('failed to restart salt minions')


    def run(self, offline=False, noprepare=False):  # noqa
        # TODO:
        #   - create a state instead
        #   -  (deprecation - rollback is not considered for R2)
        #      what about apt and other non-yum pkd managers
        #   (downgrade is another more generic option but it requires
        #    exploration of depednecies that are updated)
        # TODO (deprecation - rollback is not considered for R2)
        #      IMPROVE minions might be stopped here in case of rollback,
        #      options: set up temp ssh config and rollback yum + minion config
        #      via ssh as a fallback

        if not offline:
            # TODO plan the groups of concurrency based on:
            #   - sw list to upgrade: some sw may go before others
            #   - service discovery: nodes might be grouped per roles
            #       e.g. primaries then secondaries
            #   - phases / iterations / passes / turns:
            #       some sw might require cluster level iterations
            raise NotImplementedError(
                "Rolling upgrade is not considered for the current moment"
            )

        ret = None
        try:
            if not noprepare:
                cortx_version = GetReleaseVersion.cortx_version()
                logger.info(
                    f"Starting {'offline' if offline else 'rolling'} upgrade"
                    f" logic. Current version of CORTX: '{cortx_version}'"
                )
                self.prepare(cortx_version)

            ret = self.upgrade(offline=offline)

            cortx_version = GetReleaseVersion.cortx_version()
            logger.info(
                f"Upgrade is done."
                f" Current version of CORTX: '{cortx_version}'"
            )

            return ret
        except Exception as update_exc:
            # TODO TEST
            logger.exception('SW Upgrade failed')
            raise SWUpdateError(update_exc) from update_exc
