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

from typing import Type, Optional
import logging

from .. import (
    inputs,
    errors
)
from .deploy import (
    build_deploy_run_args,
    Deploy
)
from ..salt import function_run
from ..vendor import attr
# TODO IMPROVE EOS-8473
from ..utils import ensure
from .setup_provisioner import SetupCtx
from .configure_setup import SetupType


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
        "system.logrotate",
        "system.chrony"
    ],
    prereq=[
        "misc_pkgs.sos",
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
        "misc_pkgs.lustre"
    ],
    sync=[
        "sync.software.rabbitmq"
    ],
    iopath=[
        "motr",
        "s3server",
        "hare"
    ],
    # states to be applied in desired sequence
    controlpath=[
        "sspl",
        "uds",
        "csm"
    ],
    ha=[
        "ha.corosync-pacemaker.install",
        "ha.corosync-pacemaker.config.base",
        "ha.haproxy.start",
        "ha.cortx-ha"
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


run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class DeployDual(Deploy):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = run_args_type
    setup_ctx: Optional[SetupCtx] = None

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

    def _run_states(self, states_group: str, run_args: run_args_type):
        # FIXME VERIFY EOS-12076 Mindfulness breaks in legacy version
        setup_type = run_args.setup_type
        targets = run_args.targets
        states = deploy_states[states_group]
        stages = run_args.stages

        primary = self._primary_id()
        secondaries = f"not {primary}"

        # apply states
        if setup_type == SetupType.SINGLE:
            # TODO use salt orchestration
            for state in states:
                self._apply_state(f"components.{state}", targets, stages)
        else:
            # FIXME EOS-12076 the following logic is only
            #       for legacy dual node setup
            for state in states:
                if state in (
                    "system.storage",
                    "sspl",
                    "csm",
                    "provisioner.backup",
                    "ha.cortx-ha"
                ):
                    # Consul takes time to come online after initialization
                    # (around 2-3 mins at times). We need to ensure
                    # consul service is available before proceeding
                    # Without a healthy consul service SSPL and CSM shall fail
                    if state == "sspl":
                        self.ensure_consul_running()
                    # Execute first on secondaries then on primary.
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                    self._apply_state(f"components.{state}", primary, stages)

                elif state in (
                    "sync.software.rabbitmq",
                    "sync.software.openldap",
                    "system.storage.multipath",
                    "sync.files"
                ):
                    # Execute first on primary then on secondaries.
                    self._apply_state(f"components.{state}", primary, stages)
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                else:
                    self._apply_state(f"components.{state}", targets, stages)
                    if state == "ha.cortx-ha":
                        self.ensure_consul_running()

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
            self._run_states('sync', run_args)
            self._run_states('iopath', run_args)
            self._run_states('ha', run_args)
            self._run_states('controlpath', run_args)
            self._run_states('backup', run_args)
        else:
            if 'system' in run_args.states:
                logger.info("Deploying the system states")
                self._rescan_scsi_bus()
                self._run_states('system', run_args)

            if 'prereq' in run_args.states:
                logger.info("Deploying the prereq states")
                self._run_states('prereq', run_args)

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
