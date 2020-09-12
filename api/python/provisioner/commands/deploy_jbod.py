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
from ..vendor import attr

from .deploy import (
    build_deploy_run_args,
    Deploy
)


logger = logging.getLogger(__name__)


deploy_states = dict(
    system=[
        'system',
        'system.storage.multipath',
        'system.storage',
        'system.network',
        'system.network.data.public',
        'system.network.data.direct',
        'misc_pkgs.rsyslog',
        'system.firewall',
        'system.logrotate',
        'system.chrony'
    ],
    prereq=[
        'misc_pkgs.ssl_certs',
        'ha.haproxy.prepare',
        'ha.haproxy.install',
        'misc_pkgs.openldap.prepare',
        'misc_pkgs.openldap.install',
        'misc_pkgs.rabbitmq.install',
        'misc_pkgs.nodejs.install',
        'misc_pkgs.elasticsearch.install',
        'misc_pkgs.elasticsearch.config',
        'misc_pkgs.kibana.install',
        'misc_pkgs.statsd.install',
        'misc_pkgs.lustre.prepare',
        'misc_pkgs.lustre.install',
        'misc_pkgs.lustre.config',
        'misc_pkgs.lustre.start'
    ]
)

run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class RunArgsDeployJBOD(run_args_type):
    stages: str = attr.ib(init=False, default=None)


@attr.s(auto_attribs=True)
class DeployJBOD(Deploy):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = run_args_type

    def _run_states(self, states_group: str, run_args: run_args_type):
        # FIXME VERIFY EOS-12076 Mindfulness breaks in legacy version
        targets = run_args.targets
        states = deploy_states[states_group]
        stages = run_args.stages

        # apply states
        for state in states:
            self._apply_state(f"components.{state}", targets, stages)

    def run(self, **kwargs):
        run_args = self._run_args_type(**kwargs)

        if self._is_hw():
            # TODO EOS-12076 less generic error
            raise errors.ProvisionerError(
                "The command is specifically for VM deployment. "
                "For HW please run `deploy`"
            )

        # TODO DRY EOS-12076 copy from deploy-vm
        self._update_salt()

        if run_args.states is None:  # all states
            self._run_states('system', run_args)
            self._encrypt_pillar()
            self._run_states('prereq', run_args)
        else:
            if 'system' in run_args.states:
                logger.info("Deploying the system states")
                self._run_states('system', run_args)
                self._encrypt_pillar()

            if 'prereq' in run_args.states:
                logger.info("Deploying the prereq states")
                self._run_states('prereq', run_args)

        logger.info("Deploy JBOD - Done")
        return run_args
