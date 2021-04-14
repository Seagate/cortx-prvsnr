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
    config
)
from ..utils import run_subprocess_cmd
from ..salt import (
    local_minion_id,
    SaltSSHClient
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
from .generate_roster import (
    GenerateRoster,
    RunArgsGenerateRosterAttrs
)

logger = logging.getLogger(__name__)


deploy_states = dict(
    ha=[
        "ha.cortx-ha.teardown",
        "ha.corosync-pacemaker.teardown"
    ],
    controlpath=[
        "csm.teardown",
        "uds.teardown",
        "sspl.teardown"
    ],
    iopath=[
        "hare.teardown",
        "s3server.teardown",
        "motr.teardown"
    ],
    base_utils=[
        "cotx_utils.teardown"
    ],
    prereq=[
        "misc_pkgs.lustre.teardown",
        "misc_pkgs.statsd.teardown",
        "misc_pkgs.kibana.teardown",
        "misc_pkgs.elasticsearch.teardown",
        "misc_pkgs.nodejs.teardown",
        "misc_pkgs.rabbitmq.teardown",
        "misc_pkgs.consul.teardown",
        "misc_pkgs.openldap.teardown",
        "ha.haproxy.teardown",
        "misc_pkgs.ssl_certs.teardown"
    ],
    system=[
        "system.chrony.teardown",
        "system.logrotate.teardown",
        "system.firewall.teardown",
        "misc_pkgs.rsyslog.teadrwon",
        "system.storage.teardown",
        "system.storage.multipath.teardown",
        "system.teardown"
    ],
    bootstrap=[
        "provisioner.salt.stop",
        "system.storage.glusterfs.teardown.volume_remove",
        "system.storage.glusterfs.teardown",
        "provisioner.salt.teardown",
        "provisioner.salt.teardown.package_remove",
        "provisioner.passwordless_remove",
        "provisioner.teardown"
    ]
)

run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class SetupCtx:
    ssh_client: SaltSSHClient


@attr.s(auto_attribs=True)
class RunArgsDestroy(run_args_type):
    stages: str = attr.ib(init=False, default=None)


@attr.s(auto_attribs=True)
class DestroyNode(Deploy):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsDestroy
    _salt_ssh = None
    _temp_dir = None
    setup_ctx: Optional[SetupCtx] = None

    def _primary_id(self):
        return local_minion_id()

    def _secondaries(self):
        local_node = self._primary_id()
        secondaries = []
        node_list = PillarKey('cluster')
        pillar = PillarResolver(config.LOCAL_MINION).get([node_list])
        pillar = next(iter(pillar.values()))
        nodes = pillar[node_list]
        for key in nodes.keys():
            if 'srvnode' in key and local_node != key:
                secondaries.append(key)
        return secondaries

    @staticmethod
    def _create_ssh_client(c_path, roster_file):
        # TODO IMPROVE EOS-8473 optional support for known hosts
        ssh_options = [
            'UserKnownHostsFile=/dev/null',
            'StrictHostKeyChecking=no'
        ]
        return SaltSSHClient(
            c_path=c_path,
            roster_file=roster_file,
            ssh_options=ssh_options
        )

    def _apply_states(self, state, targets=None):
        try:
            if targets:
                self.setup_ctx.ssh_client.state_apply(
                    f"components.{state}",
                    targets=targets,
                    tgt_type='pcre'
                )
            else:
                self.setup_ctx.ssh_client.state_apply(
                    f"components.{state}"
                )
        except Exception as exc:
            logger.warn(f"Failed {state} on {targets} Error: {str(exc)}")

    def _run_cmd(self, cmds, targets=None):
        for cmd in cmds:
            logger.info(f"Running command {cmd} ")
            try:
                if targets:
                    self.setup_ctx.ssh_client.cmd_run(
                        f"{cmd}",
                        targets=targets,
                        tgt_type='pcre'
                    )
                else:
                    self.setup_ctx.ssh_client.cmd_run(
                        f"{cmd}"
                    )
            except Exception as exc:
                logger.warn(f"Failed cmd {cmd} on {targets} Error: {str(exc)}")

    def _run_states(self,  # noqa: C901 FIXME
        states_group: str, run_args: run_args_type):
        setup_type = run_args.setup_type
        targets = run_args.targets
        states = deploy_states[states_group]
        primary = self._primary_id()
        secondaries = self._secondaries()

        # apply states
        for state in states:
            if setup_type == SetupType.SINGLE:
                if (
                    state == "system.storage.multipath.teardown" and
                    self._is_hw()
                ):
                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                elif state not in (
                    "system.storage.glusterfs.teardown.volume_remove",
                    "system.storage.glusterfs.teardown",
                    "provisioner.salt.teardown.package_remove",
                    "system.storage.multipath.teardown",
                    "provisioner.passwordless_remove"
                ):
                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

            else:
                if (
                    state == "system.storage.multipath.teardown" and
                    self._is_hw()
                ):
                    logger.info(f"Applying '{state}' on {secondaries}")
                    # Execute first on secondaries then on primary.
                    self._apply_states(state, '|'.join(secondaries))

                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                if state in (
                    "system.storage.glusterfs.teardown.volume_remove",
                    "provisioner.teardown",
                    "provisioner.passwordless_remove",
                    "misc_pkgs.openldap.teardown",
                    "misc_pkgs.rabbitmq"
                ):

                    logger.info(f"Applying '{state}' on {secondaries}")
                    # Execute first on secondaries then on primary.
                    self._apply_states(state, '|'.join(secondaries))

                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                elif state in (
                    "ha.cortx-ha.teardown",
                    "sspl.teardown"
                ):
                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                    logger.info(f"Applying '{state}' on {secondaries}")
                    # Execute first on secondaries then on primary.
                    self._apply_states(state, '|'.join(secondaries))

                elif state in (
                    "provisioner.salt.teardown.package_remove",
                    "provisioner.passwordless_remove"
                ):
                    logger.info(f"Applying '{state}' on {secondaries}")
                    # Execute first on secondaries then on primary.
                    self._apply_states(state, '|'.join(secondaries))
                else:
                    logger.info(f"Applying '{state}' on {targets}")
                    self._apply_states(state)

    def run(self, **kwargs):  # noqa: C901
        run_args = self._run_args_type(**kwargs)
        temp_dir = config.PRVSNR_TMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)

        salt_config_master = str(
            '/etc/salt/master'
        )

        # we cannot put roster file in profile or etc
        # as we are removing these dir in case of bootstrap
        roster = str(
            temp_dir / 'roster'
        )

        roster_params = attr.asdict(RunArgsGenerateRosterAttrs())
        roster_params['roster_path'] = roster
        GenerateRoster().run(**roster_params)

        ssh_client = DestroyNode._create_ssh_client(salt_config_master, roster)

        self.setup_ctx = SetupCtx(ssh_client)

        if len(self._secondaries()):
            run_args.setup_type = SetupType.GENERIC

        # Need to remove cache and few dir manually
        list_cmds = ["rm -rf /var/cache/salt/"]
        list_cmds.append(f"rm -rf {str(config.profile_base_dir().parent)}")
        list_cmds.append(f"rm -rf {config.CORTX_ROOT_DIR}")
        list_cmds.append(f"rm -rf {config.PRVSNR_DATA_SHARED_DIR}")
        list_cmds.append("yum remove -y salt salt-minion salt-master")

        if run_args.states is None:  # all states
            self._run_states('ha', run_args)
            self._run_states('controlpath', run_args)
            self._run_states('iopath', run_args)
            self._run_states('prereq', run_args)
            self._run_states('base_utils', run_args)
            self._run_states('system', run_args)
            self._run_states('bootstrap', run_args)
            self._run_cmd(list_cmds)
        else:
            if 'bootstrap' in run_args.states:
                logger.info("Teardown Provisioner Bootstrapped Environment")
                self._run_states('bootstrap', run_args)
                self._run_cmd(list_cmds)

            if 'system' in run_args.states:
                logger.info("Teardown the system states")
                self._run_states('system', run_args)

            if 'base_utils' in run_args.states:
                logger.info("Teardown Provisioner base_utils states")
                self._run_states('base_utils', run_args)
                self._run_cmd(list_cmds)

            if 'prereq' in run_args.states:
                logger.info("Teardown the prereq states")
                self._run_states('prereq', run_args)

            if 'iopath' in run_args.states:
                logger.info("Teardown the io path states")
                self._run_states('iopath', run_args)

            if 'ha' in run_args.states:
                logger.info("Teardown the ha path states")
                self._run_states('ha', run_args)

            if 'controlpath' in run_args.states:
                logger.info("Teardown the control path states")
                self._run_states('controlpath', run_args)

        logger.info("Destroy VM - Done")
        run_subprocess_cmd(f"rm -rf {str(temp_dir)}")
        return run_args
