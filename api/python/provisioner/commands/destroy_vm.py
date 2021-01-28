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

from typing import Type
import logging

from .. import (
    inputs,
    errors,
    config,
    ALL_MINIONS
)
from ..utils import run_subprocess_cmd
from ..salt import local_minion_id
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
    prvsnr=[
        "system.storage.glusterfs.teardown.volume_remove",
        "system.storage.glusterfs.teardown"
    ]
)

run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class RunArgsDestroy(run_args_type):
    stages: str = attr.ib(init=False, default=None)


@attr.s(auto_attribs=True)
class DestroyNode(Deploy):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsDestroy

    @staticmethod
    def remove_prvsnr(nodes):
        for node in nodes:
            if local_minion_id() == node:
                logger.info(f"remove cortx-prvsnr rpms on {node}")
                run_subprocess_cmd(
                    f"ssh {node} yum erase -y cortx-prvsnr")
            else:
                logger.info(
                    f"remove cortx-prvsnr python36-cortx-prvsnr on {node}")
                run_subprocess_cmd(
                    f"ssh {node} yum erase -y"
                    "cortx-prvsnr python36-cortx-prvsnr")

    @staticmethod
    def remove_passwordless_ssh(nodes):
        for node in nodes:
            logger.info(f"Remove passwordless configuration with {node}")
            run_subprocess_cmd(
                f"rm -rf /root/.ssh")

    @staticmethod
    def remove_salt(nodes):
        salt_cache_dir = '/var/cache/salt'
        salt_config = '/etc/salt'

        for node in nodes:
            logger.info(f"stopping salt-minion/salt-master on {node}")
            run_subprocess_cmd(
                f"ssh {node} systemctl stop salt-minion salt-master")

            logger.info(f"remove salt rpms on {node}")
            run_subprocess_cmd(
                f"ssh {node} yum erase -y salt-minion salt-master salt")

            logger.info(f"Removing salt from node {node}")
            run_subprocess_cmd(f"ssh {node} rm -rf {salt_cache_dir}")
            run_subprocess_cmd(f"ssh {node} rm -rf {salt_config}")

    @staticmethod
    def remove_dir(list_dir, nodes):
        for node in nodes:
            for di in list_dir:
                logger.info(f"cleaning up {di} dir on {node}")
                run_subprocess_cmd(f"ssh {node} rm -rf {di}")

    def _run_states(self, states_group: str, run_args: run_args_type):
        setup_type = run_args.setup_type
        targets = run_args.targets
        states = deploy_states[states_group]
        stages = run_args.stages
        primary = self._primary_id()
        secondaries = f"not {primary}"
        nodes = []

        if states_group == 'prvsnr' and targets == ALL_MINIONS:
            node_list = PillarKey('cluster/node_list')
            pillar = PillarResolver(config.LOCAL_MINION).get([node_list])
            pillar = next(iter(pillar.values()))
            nodes = pillar[node_list]
        else:
            nodes.append(targets)

        # apply states
        for state in states:
            if setup_type == SetupType.SINGLE and state not in (
                "system.storage.glusterfs.teardown.volume_remove",
                "system.storage.glusterfs.teardown"
            ):
                self._apply_state(f"components.{state}", primary, stages)
            else:
                if state == "system.storage.glusterfs.teardown.volume_remove":
                    # Execute first on secondaries then on primary.
                    self._apply_state(
                        f"components.{state}", secondaries, stages
                    )
                    self._apply_state(f"components.{state}", primary, stages)
                else:
                    self._apply_state(f"components.{state}", targets, stages)

        # salt will not be available so handle teardown using subprocess
        if states_group == 'prvsnr':
            list_dir = []
            list_dir.append(str(config.profile_base_dir().parent))
            list_dir.append(config.CORTX_ROOT_DIR)
            DestroyNode.remove_prvsnr(nodes)
            DestroyNode.remove_dir(list_dir, nodes)
            DestroyNode.remove_salt(nodes)
            DestroyNode.remove_passwordless_ssh(nodes)

    def run(self, **kwargs):  # noqa: C901
        run_args = self._run_args_type(**kwargs)

        if self._is_hw():
            raise errors.ProvisionerError(
                "The command is specifically for VM teardown. "
            )

        if run_args.states is None:  # all states
            self._run_states('prvsnr', run_args)

        else:
            if 'prvsnr' in run_args.states:
                logger.info("Teardown Provisioner Bootstrapped Environment")
                self._run_states('prvsnr', run_args)
            else:
                raise NotImplementedError(
                    'Only prvsnr state is supported for now'
                )

        logger.info("Destroy VM - Done")
        return run_args
