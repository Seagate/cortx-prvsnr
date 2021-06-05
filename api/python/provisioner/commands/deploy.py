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

from typing import Type, Dict, List, Optional
import logging

from .. import (
    config,
    inputs,
    errors
)
from ..salt import (
    function_run,
    cmd_run,
    StatesApplier,
    local_minion_id,
    sls_exists
)
from ..vendor import attr
from ..utils import ensure
# TODO IMPROVE EOS-8473

from . import (
    RunArgsUpdate,
    CommandParserFillerMixin
)
from .setup_provisioner import SetupCtx
from .configure_setup import (
    RunArgsConfigureSetupAttrs,
    SetupType
)


logger = logging.getLogger(__name__)


deploy_states = dict(
    system=[
        "system",
        "system.storage.multipath",
        "system.storage",
        "system.network",
        "system.network.data.public",
        "system.network.data.direct",
        "misc_pkgs.rsyslog",
        "system.firewall",
        "system.firewall.sanity_check",
        "system.logrotate",
        "system.chrony"
    ],
    prereq=[
        "misc_pkgs.sos",
        "misc_pkgs.ipmi.bmc_watchdog",
        "misc_pkgs.ssl_certs",
        "ha.haproxy",
        "misc_pkgs.openldap",
        "misc_pkgs.rabbitmq",
        "misc_pkgs.nodejs",
        "misc_pkgs.kafka",
        "misc_pkgs.elasticsearch",
        "misc_pkgs.kibana",
        "misc_pkgs.statsd",
        "misc_pkgs.consul.install",
        "misc_pkgs.lustre",
        "misc_pkgs.consul.install",
        "ha.corosync-pacemaker.install",
        "ha.corosync-pacemaker.config.base"
    ],
    utils=[
        "cortx_utils"
    ],
    sync=[
        "sync.software.rabbitmq"
    ],
    iopath=[
        "motr",
        "s3server",
        "hare"
    ],
    ha=[
        "ha.cortx-ha"
    ],
    # states to be applied in desired sequence
    controlpath=[
        "sspl",
        "uds",
        "csm"
    ],
    backup=[
        "provisioner.backup",
        "motr.backup",
        "s3server.backup",
        "hare.backup",
        "ha.iostack-ha.backup",
        "sspl.backup",
        "csm.backup"
    ]
)


def build_deploy_run_args(deploy_states: Dict):
    # TODO TEST EOS-12076
    @attr.s(auto_attribs=True)
    class _RunArgsDeploy(RunArgsUpdate):
        setup_type: str = RunArgsConfigureSetupAttrs.setup_type
        states: str = attr.ib(
            metadata={
                inputs.METADATA_ARGPARSER: {
                    'help': (
                        "deploy specific state groups, "
                        "might be used multiple times to specify multiple "
                        "groups, if not specified - all states are considered"
                    ),
                    'choices': list(deploy_states),
                    'action': 'append',
                    'metavar': 'state'
                }
            },
            default=None,
            # TODO IMPROVE EOS-12076 more accurate converter
            converter=(lambda states: set(states) if states else None)
        )
        stages: str = attr.ib(
            metadata={
                inputs.METADATA_ARGPARSER: {
                    'help': (
                        "apply only specific stages, "
                        "might be used multiple times to specify multiple "
                        "stages, if not specified - all are considered"
                    ),
                    'choices': [
                        'install',
                        'config',
                        'start',
                        'sanity_check'
                    ],
                    'action': 'append',
                    'metavar': 'stage'
                }
            },
            default=None,
            # TODO IMPROVE EOS-12076 more accurate converter
            converter=(lambda states: set(states) if states else None)
        )
    return _RunArgsDeploy


run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class Deploy(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = run_args_type
    setup_ctx: Optional[SetupCtx] = None

    def _primary_id(self):
        if self.setup_ctx:
            return self.setup_ctx.run_args.primary.minion_id
        else:
            return local_minion_id()

    def _sls_exists(
        self, state, targets=config.ALL_MINIONS, summary_only=True
    ):
        if self.setup_ctx:
            try:
                self.setup_ctx.ssh_client.cmd_run(
                    (
                        f"salt -C '{targets}' state.sls_exists {state}"
                    ), targets=self._primary_id()
                )
            # TODO IMPROVE EOS-12076 more accurate errors processing
            except errors.SaltCmdResultError:
                return False
            else:
                return True
        else:
            return sls_exists(state, targets=targets, tgt_type='compound')

    def _function_run(self, fun, targets=config.ALL_MINIONS):
        if self.setup_ctx:
            return self.setup_ctx.ssh_client.cmd_run(
                (
                    f"salt -C '{targets}' {fun}"
                ), targets=self._primary_id()
            )
        else:
            return function_run(fun, targets=targets, tgt_type='compound')

    def _cmd_run(self, cmd, targets=config.ALL_MINIONS):
        if self.setup_ctx:
            # TODO IMPROVE EOS-12076 consider to use salt-ssh client's
            #      mcd_run directly but it woudl require accurate targeting
            #      since salt-ssh targets differ from remote salt's ones
            return self.setup_ctx.ssh_client.cmd_run(
                (
                    f"salt -C '{targets}' cmd.run '{cmd}'"
                ), targets=self._primary_id()
            )
        else:
            return cmd_run(cmd, targets=targets, tgt_type='compound')

    def _is_hw(self):
        if self.setup_ctx:
            res = self.setup_ctx.ssh_client.run(
                'pillar.get',
                fun_args=['setup:grains:hostname_status:Chassis'],
                targets=self._primary_id()
            )
        else:
            res = function_run(
                'pillar.get',
                fun_args=['setup:grains:hostname_status:Chassis'],
                targets=self._primary_id()
            )

        return res[self._primary_id()] == 'server'

    def _apply_state(
        self, state, targets=config.ALL_MINIONS, stages: Optional[List] = None
    ):
        if stages is None:
            logger.info(f"Applying '{state}' on {targets}")
            if self.setup_ctx:
                return self.setup_ctx.ssh_client.cmd_run(
                    (
                        f"salt -C '{targets}' state.apply {state} --out=json"
                    ), targets=self._primary_id()
                )
            else:
                return StatesApplier.apply(
                    [state], targets, tgt_type='compound'
                )
        else:
            for stage in stages:
                _state = f"{state}.{stage}"
                if self._sls_exists(_state, targets=targets):
                    return self._apply_state(_state, targets)
                else:
                    logger.warning(f"State {_state} is missed, ignored")

    def _run_states(self, states_group: str, run_args: run_args_type):
        # FIXME VERIFY EOS-12076 Mindfulness breaks in legacy version
        setup_type = (
            SetupType.SINGLE
            if (1 == len(run_args.targets))
            else (run_args.setup_type
                  if run_args.setup_type
                  else SetupType.GENERIC)

        )
        targets = run_args.targets
        states = deploy_states[states_group]
        stages = run_args.stages

        primary = self._primary_id()
        secondaries = f"not {primary}"

        hw_states = [
            "system.storage.multipath",
            "misc_pkgs.ipmi.bmc_watchdog",
        ]

        # apply states
        for state in states:

            if state in hw_states and not self._is_hw():
                continue

            if setup_type == SetupType.SINGLE:
                # TODO use salt orchestration
                if "sync" not in state:
                    self._apply_state(f"components.{state}", targets, stages)
            else:
                if state in (
                    "system.storage",
                    "sspl",
                ):
                    # Execute first on secondaries then on primary.
                    if state == "sspl":
                        self.ensure_consul_running()
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                    self._apply_state(f"components.{state}", primary, stages)

                elif state in (
                    "sync.software.rabbitmq",
                    "sync.software.openldap",
                    "system.storage.multipath",
                    "sync.files",
                    "ha.cortx-ha"
                ):
                    if state == "ha.cortx-ha":
                        self.ensure_consul_running()
                    self._apply_state(f"components.{state}", primary, stages)
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                else:
                     # Execute on all targets
                    self._apply_state(f"components.{state}", targets, stages)

    def _update_salt(self, targets=config.ALL_MINIONS):
        # TODO IMPROVE why do we need that
        # TODO IMPROVE do wee need to wait 2 seconds after each operation
        #      as it was in legacy bash script
        logger.info("Updating Salt data")

        self._apply_state("components.system.config.sync_salt", targets)

    def _encrypt_pillar(self):
        # FIXME ??? EOS-12076 targets
        # Encrypt passwords in pillar data
        logger.info("Encrypting salt pillar data")

        self._apply_state(
            "components.system.config.pillar_encrypt",
            self._primary_id())

    def _destroy_storage(self, run_args, nofail=True):
        targets = run_args.targets

        # Old remnant partitios from previous deployments has to be cleaned-up
        logger.info("Removing components.system.storage from all nodes.")
        self._apply_state("components.system.storage.teardown", targets)

    def _rescan_scsi_bus(self, targets=config.ALL_MINIONS, nofail=True):
        if self._is_hw():
            logger.info("Rescan SCSI bus")
            try:
                return self._cmd_run("rescan-scsi-bus.sh", targets=targets)
            except errors.SaltCmdResultError:
                logger.exception("rescan-scsi-bus.sh failed")
                if not nofail:
                    raise

    def check_consul_running(self):
        consul_map = {"srvnode-1": "hare-consul-agent-c1",
                      "srvnode-2": "hare-consul-agent-c2"}
        result_flag = True
        for target in consul_map:
            if self.setup_ctx:
                res = self.setup_ctx.ssh_client.run(
                    'service.status',
                    fun_args=[consul_map[target]],
                    targets=target
                )
            else:
                res = function_run(
                    'service.status',
                    fun_args=[consul_map[target]],
                    targets=target
                )

            if not res[target]:
                result_flag = False
                logger.info(f"Consul is not running on {target}")
        if result_flag:
            logger.info("Consul found running on respective nodes.")
            return True

    def ensure_consul_running(self, tries=15, wait=5):
        logger.info("Validating availability of hare-consul-agent.")
        try:
            ensure(self.check_consul_running, tries=tries, wait=wait)
        except errors.ProvisionerError:
            logger.error("Unable to get healthy hare-consul-agent service "
                         "Exiting further deployment...")
            raise errors.ProvisionerError("Unable to get healthy "
                                          "hare-consul-agent service.")

    def run(self, **kwargs):  # noqa: C901 FIXME
        run_args = self._run_args_type(**kwargs)

        # FIXME EOS-12076 in case of dual node some operations (destroy)
        #       should be performed on non primary nodes

        self._update_salt()

        if run_args.stages is not None:
            raise NotImplementedError(
                'no partial stages appliance is supported for now'
            )

        if run_args.states is None:  # all states

            self._rescan_scsi_bus()
            self._run_states('system', run_args)
            self._run_states('prereq', run_args)
            self._run_states('utils', run_args)
            self._run_states('sync', run_args)
            self._run_states('iopath', run_args)
            self._run_states('ha', run_args)
            self._run_states('controlpath', run_args)
            # self._run_states('backup', run_args)
        else:
            if 'system' in run_args.states:
                logger.info("Deploying the system states")
                self._rescan_scsi_bus()
                self._run_states('system', run_args)

            if 'prereq' in run_args.states:
                logger.info("Deploying the prereq states")
                self._run_states('prereq', run_args)

            if 'utils' in run_args.states:
                logger.info("Deploying the foundation states")
                self._run_states('utils', run_args)

            if 'sync' in run_args.states:
                logger.info("Deploying the sync states")
                self._run_states('sync', run_args)

            if 'iopath' in run_args.states:
                logger.info("Deploying the io path states")
                self._run_states('iopath', run_args)

            if 'ha' in run_args.states:
                logger.info("Deploying the ha states")
                self._run_states('ha', run_args)

            if 'controlpath' in run_args.states:
                logger.info("Deploying the control path states")
                self._run_states('controlpath', run_args)

            if 'backup' in run_args.states:
                logger.info("Deploying the backup states")
                self._run_states('backup', run_args)

        logger.info("Deploy - Done")
        return run_args
