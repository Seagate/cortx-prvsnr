#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

from typing import Type
import logging

from .. import (
    inputs,
    errors
)
from ..salt import (
    cmd_run,
    local_minion_id,
    StateFunExecuter
)
from ..pillar import (
    PillarKey,
    PillarResolver
)
from ..vendor import attr
# TODO IMPROVE EOS-8473

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
        "system.logrotate",
        "system.ntp"
    ],
    prereq=[
        "misc_pkgs.ssl_certs",
        "ha.haproxy",
        "misc_pkgs.openldap",
        "misc_pkgs.rabbitmq",
        "misc_pkgs.nodejs",
        "misc_pkgs.elasticsearch",
        "misc_pkgs.kibana",
        "misc_pkgs.statsd"
    ],
    sync=[
        "sync.software.openldap",
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
        "csm",
        "uds"
    ]
)

run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class DeployVM(Deploy):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = run_args_type

    def _run_states(self, states_group: str, run_args: run_args_type):
        # FIXME VERIFY EOS-12076 Mindfulness breaks in legacy version
        setup_type = run_args.setup_type
        targets = run_args.targets
        states = deploy_states[states_group]
        stages = run_args.stages

        primary = local_minion_id()
        secondaries = f"not {primary}"

        # apply states
        for state in states:
            # TODO use salt orchestration
            if setup_type == SetupType.SINGLE:
                self._apply_state(f"components.{state}", targets, stages)
            else:
                # FIXME EOS-12076 the following logic is only
                #       for legacy dual node setup
                if state == "sspl":
                    # Execute first on secondaries then on primary.
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                    self._apply_state(f"components.{state}", primary, stages)

                elif state in (
                    "sync.software.rabbitmq",
                    "sync.software.openldap"
                ):
                    # Execute first on primary then on secondaries.
                    self._apply_state(f"components.{state}", primary, stages)
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                else:
                    self._apply_state(f"components.{state}", targets, stages)

            if state == "hare":
                logger.info("Bootstraping cluster")
                cmd_run(
                    "hctl bootstrap --mkfs /var/lib/hare/cluster.yaml",
                    targets=local_minion_id()
                )

    def run(self, **kwargs):
        run_args = self._run_args_type(**kwargs)

        if self._is_hw():
            # TODO EOS-12076 less generic error
            raise errors.ProvisionerError(
                "The command is specifically for VM deployment. "
                "For HW please run `deploy`"
            )

        self._update_salt()

        if run_args.states is None:  # all states
            self._run_states('system', run_args)
            self._encrypt_pillar()
            self._run_states('prereq', run_args)

            if run_args.setup_type != SetupType.SINGLE:
                self._run_states('sync', run_args)

            self._run_states('iopath', run_args)
            self._run_states('controlpath', run_args)
        else:
            if 'system' in run_args.states:
                logger.info("Deploying the system states")
                self._run_states('system', run_args)
                self._encrypt_pillar()

            if 'prereq' in run_args.states:
                logger.info("Deploying the prereq states")
                self._run_states('prereq', run_args)

            if (
                'sync' in run_args.states or
                run_args.setup_type != SetupType.SINGLE
            ):
                logger.info("Deploying the sync states")
                self._run_states('sync', run_args)

            if 'iopath' in run_args.states:
                logger.info("Recreating the metadata partitions")
                self._apply_state(
                    "components.system.storage",
                    run_args.targets,
                    run_args.stages
                )

                if run_args.setup_type != SetupType.SINGLE:
                    metadata_device_keypath = PillarKey(
                        f"cluster/{local_minion_id()}/storage/metadata_device"
                    )
                    logger.info(
                        f"Resolving pillar key {metadata_device_keypath}"
                    )
                    pillar = PillarResolver(local_minion_id()).get(
                        [metadata_device_keypath]
                    )
                    metadata_device = pillar[local_minion_id()][0]
                    metadata_device = f"{metadata_device}1"
                    # TODO IMPROVE EOS-12076 hard coded
                    mount_point = '/var/mero'

                    logger.info(
                        f"Mounting partition {metadata_device} "
                        "into {mount_point} (with fstab record)"
                    )
                    StateFunExecuter.execute(
                        'mount.mounted',
                        fun_args=[mount_point, metadata_device, 'ext4'],
                        fun_kwargs=dict(mkmnt=True, persist=True)
                    )

                logger.info("Deploying the io path states")
                self._run_states('iopath', run_args)

            if 'ctrlpath' in run_args.states:
                logger.info("Deploying the control path states")
                self._run_states('controlpath', run_args)

        logger.info("Deploy VM - Done")
        return run_args
