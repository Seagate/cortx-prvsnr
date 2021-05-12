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
from ..salt import StateFunExecuter
from ..pillar import (
    PillarKey,
    PillarResolver
)
from ..vendor import attr
# TODO IMPROVE EOS-8473

from .setup_provisioner import SetupCtx
from .configure_setup import (
    SetupType
)
from .deploy import (
    build_deploy_run_args,
    Deploy
)


logger = logging.getLogger(__name__)


deploy_states = dict(
    system=[
        "system",
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
        "misc_pkgs.ssl_certs",
        "ha.haproxy",
        "misc_pkgs.openldap",
        "misc_pkgs.rabbitmq",
        "misc_pkgs.nodejs",
        "misc_pkgs.kafka",
        "misc_pkgs.elasticsearch",
        "misc_pkgs.kibana",
        "misc_pkgs.statsd",
        "misc_pkgs.consul.install"
    ],
    utils=[
        "cortx_utils"
    ],
    sync=[
        "sync.software.rabbitmq"
    ],
    iopath=[
        "misc_pkgs.lustre",
        "motr",
        "s3server",
        "hare"
    ],
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
    ]
)

run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class DeployVM(Deploy):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = run_args_type
    setup_ctx: Optional[SetupCtx] = None

    @staticmethod
    def _get_node_list():
        """Retrieve pillar data."""
        pillar_key = PillarKey("cluster")
        pillar = PillarResolver(config.LOCAL_MINION).get([pillar_key])
        pillar = next(iter(pillar.values()))
        if not pillar[pillar_key] or pillar[pillar_key] is values.MISSED:
            raise ValueError(f"value is not specified for {key}")
        else:
            cluster = pillar[pillar_key]
            nodes = []
            for key in cluster:
                if 'srvnode' in key:
                    nodes.append(key)
            return nodes 

    def _run_states(self, states_group: str, run_args: run_args_type):
        # FIXME VERIFY EOS-12076 Mindfulness breaks in legacy version
        setup_type = run_args.setup_type
        targets = run_args.targets
        states = deploy_states[states_group]
        stages = run_args.stages

        primary = self._primary_id()
        secondaries = f"not {primary}"

        # apply states
        for state in states:
            # TODO use salt orchestration
            if setup_type == SetupType.SINGLE:
                logger.debug("Executing for single node.")
                if not state.startswith("sync"):
                    self._apply_state(f"components.{state}", primary, stages)
            else:
                logger.debug("Executing for multiple nodes.")
                # FIXME EOS-12076 the following logic is only
                #       for legacy dual node setup
                if state in (
                    "sspl",
                ):
                    # Execute first on secondaries then on primary.
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                    self._apply_state(f"components.{state}", primary, stages)

                elif state in (
                    "sync.software.rabbitmq",
                    "sync.software.openldap",
                    "csm",
                    "ha.cortx-ha"
                ):
                    # Execute first on primary then on secondaries.
                    self._apply_state(f"components.{state}", primary, stages)
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                elif state in (
                    "ha.cortx-ha"
                ):
                    # Execute first on primary then on secondaries sequentially.
                    nodes = DeployVM._get_node_list()
                    self._apply_state(f"components.{state}", primary, stages)
                    if primary in nodes:
                        nodes.remove(primary)
                    for node in nodes:
                        self._apply_state(f"components.{state}", node, stages)
                else:
                    self._apply_state(f"components.{state}", targets, stages)

    def run(self, **kwargs):  # noqa: C901
        run_args = self._run_args_type(**kwargs)

        if self._is_hw():
            # TODO EOS-12076 less generic error
            logger.error(
                "Setup Type is HW. Executed command is specific for VM. "
                "For HW please run `deploy`"
            )
            raise errors.ProvisionerError(
                "The command is specifically for VM deployment. "
                "For HW please run `deploy`"
            )

        self._update_salt()

        if run_args.states is None:  # all states
            self._run_states('system', run_args)
            self._run_states('prereq', run_args)
            self._run_states('utils', run_args)

            if run_args.setup_type != SetupType.SINGLE:
                self._run_states('sync', run_args)

            self._run_states('iopath', run_args)
            self._run_states('controlpath', run_args)
            self._run_states('ha', run_args)
        else:
            if 'system' in run_args.states:
                logger.info("Deploying the system states")
                self._run_states('system', run_args)

            if 'prereq' in run_args.states:
                logger.info("Deploying the prereq states")
                self._run_states('prereq', run_args)

            if 'utils' in run_args.states:
                logger.info("Deploying foundation states")
                self._run_states('utils', run_args)

            if (
                'sync' in run_args.states and
                run_args.setup_type != SetupType.SINGLE
            ):
                logger.info("Deploying the sync states")
                self._run_states('sync', run_args)

            if 'iopath' in run_args.states:
                logger.info("Deploying the io path states")
                self._run_states('iopath', run_args)

            if 'controlpath' in run_args.states:
                logger.info("Deploying the control path states")
                self._run_states('controlpath', run_args)

            if 'ha' in run_args.states:
                logger.info("Deploying the ha path states")
                self._run_states('ha', run_args)

        logger.info("Deploy VM - Done")
        return run_args
