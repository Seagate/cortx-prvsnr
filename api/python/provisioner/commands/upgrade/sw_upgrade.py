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
from provisioner import config
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
from provisioner.commands.mini_api import (
    EventRaiser
)
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

from provisioner import errors
from provisioner.cortx_ha import (
    cluster_stop,
    cluster_start,
    is_cluster_healthy
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
        if not is_cluster_healthy():
            raise errors.ProvisionerError('cluster is not healthy')

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
            targets=config.ALL_MINIONS, multiple_targets_ok=True
        )
        logger.debug("Current list of yum txn ids: {txn_ids_dict}")

        PillarSet().run(
            f"upgrade/yum_snapshots/{cortx_version}",
            txn_ids_dict
        )

    def self_upgrade(self, flow=config.CortxFlows.UPGRADE):
        # here we can use python API (SWUpgradeNode) since
        # old provisioner version would be called anyway
        logger.info('Upgrading Provisioner on all the nodes')
        SWUpgradeNode().run(flow=flow, sw=['provisioner'], no_events=True)

        # support for a separate orchestrator module
        # todo: can be a python API call if no changes for provisioner
        # logger.info('Upgrading Orchestrator on all the nodes')
        # cmd_run('provisioner sw_upgrade_node --sw orchestrator')

    def delegate(self, flow=config.CortxFlows.UPGRADE):
        logger.info(
            "SW Upgrade: delegating remaing phases"
            " to upgraded orchestrator logic"
        )
        return cmd_run(
            "provisioner sw_upgrade --noprepare"
            f"{'' if (flow == config.CortxFlows.UPGRADE) else ' --offline'}"
        )

    def plan_upgrade(self, flow=config.CortxFlows.UPGRADE):
        res = []

        logger.info("SW Upgrade Plan Build")
        if flow == config.CortxFlows.UPGRADE:
            raise NotImplementedError("Not considered for the current moment")
        else:
            # trivial - all nodes in parallel
            res = [list_minions()]

        logger.info(f"Upgrade plan is: '{res}'")
        return res

    def upgrade_cluster(
        self,
        planned_node_groups: List[List[str]],
        flow=config.CortxFlows.UPGRADE
    ):
        logger.info("Fire pre-upgrade event (cluster level)")
        # Assumptions:
        #   resources cleanup and final cluster stop of should
        #   happen as part of pre-uprgade HA call
        EventRaiser(
            event=config.event_name(
                config.MiniAPIHooks.UPGRADE, config.MiniAPIEvents.PRE
            ),
            flow=flow,
            level=config.MiniAPILevels.CLUSTER
        ).run()

        # the following needed only in case pacemaker is upgraded
        # logger.info("Stopping the Cortx cluster")
        # cluster_stop(standby=False)

        for group in planned_node_groups:
            logger.info(f"Upgrading nodes: '{group}'")
            # XXX ??? provisioner (orchestrator) have been already
            #         upgraded, do we need to upgrade them here?
            SWUpgradeNode().run(flow=flow, targets=group)

        # the following needed only in case pacemaker is upgraded
        # logger.info("Stopping the Cortx cluster")
        # cluster_start(unstandby=True)

        logger.info("Fire post-upgrade event (cluster level)")
        EventRaiser(
            event=config.event_name(
                config.MiniAPIHooks.UPGRADE, config.MiniAPIEvents.POST
            ),
            flow=flow,
            level=config.MiniAPILevels.CLUSTER
        ).run()

    def prepare(self, cortx_version, flow=config.CortxFlows.UPGRADE):
        self.validate()

        self.backup(cortx_version)

        self.self_upgrade(flow=flow)

    def upgrade(self, flow=config.CortxFlows.UPGRADE):
        # TODO: can skip that if no changes for Orchestrator
        ret = cmd_run('provisioner --version')
        new_prvsnr_version = next(iter(ret.values()))
        # Note. assumption: case new version < old version is validated
        #       as part of validate stage
        if new_prvsnr_version != __version__:
            return self.delegate(flow=flow)
        else:
            logger.info(
                "SW Upgrade upgraded logic is the same as the"
                " current one, proceeding without delegation"
            )

        # noprepare is True or new logic is the same
        planned_node_groups = self.plan_upgrade(flow=flow)

        logger.info("Moving the Cortx cluster into standby mode")
        cluster_stop(standby=True)

        self.upgrade_cluster(planned_node_groups, flow=flow)

        logger.info("Starting the Cortx cluster")
        cluster_start()
        # cluster_start(unstandby=False)

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

        flow = (
            config.CortxFlows.UPGRADE_OFFLINE if offline
            else config.CortxFlows.UPGRADE
        )

        if flow == config.CortxFlows.UPGRADE:
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
                    f"Starting"
                    f" {'rolling' if (flow == config.CortxFlows.UPGRADE) else 'offline'}"  # noqa: E501
                    " upgrade logic."
                    f" Current version of CORTX: '{cortx_version}'"
                )
                self.prepare(cortx_version)

            ret = self.upgrade(flow=flow)

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
