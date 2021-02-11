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
    errors,
    config
)
from ..utils import run_subprocess_cmd
from ..vendor import attr
# TODO IMPROVE EOS-8473

from .configure_setup import (
    SetupType
)
from .destroy_vm import (
    DestroyNode,
    SetupCtx
)
from .deploy import (
    build_deploy_run_args
)


logger = logging.getLogger(__name__)


deploy_states = dict(
    ha=[
        "ha.cortx-ha.teardown",
        "ha.corosync-pacemaker.teardown",
        "hare.teardown"
    ],
    controlpath=[
        "ha.ctrlstack-ha.teardown",
        "csm.teardown",
        "uds.teardown",
        "sspl.teardown"
    ],
    iopath=[
        "s3server.teardown",
        "motr.teardown",
        "misc_pkgs.lustre.teardown"
    ],
    prereq=[
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
        "provisioner.salt.teardown.stop",
        "system.storage.glusterfs.teardown.volume_remove",
        "system.storage.glusterfs.teardown",
        "provisioner.salt.teardown",
        "provisioner.salt.teardown.package_remove",
        "provisioner.teardown",
        "provisioner.passwordless_remove"
    ]
)

run_args_type = build_deploy_run_args(deploy_states)


@attr.s(auto_attribs=True)
class RunArgsDestroy(run_args_type):
    stages: str = attr.ib(init=False, default=None)


@attr.s(auto_attribs=True)
class DestroyHW(DestroyNode):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsDestroy
    _temp_dir = None
    setup_ctx: Optional[SetupCtx] = None

    def _run_states(self,
        states_group: str, run_args: run_args_type):  # noqa: C901 FIXME
        setup_type = run_args.setup_type
        targets = run_args.targets
        states = deploy_states[states_group]
        primary = self._primary_id()
        secondaries = self._secondaries()

        # apply states
        for state in states:
            if setup_type == SetupType.SINGLE:
                if state not in (
                    "system.storage.glusterfs.teardown.volume_remove",
                    "system.storage.glusterfs.teardown",
                    "provisioner.salt.teardown.package_remove"
                ):
                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                    if state == "provisioner.passwordless_remove":
                        list_dir = ["/var/cache/salt/"]
                        list_pkgs = ["salt", "salt-minion", "salt-master"]
                        list_dir.append(str(config.profile_base_dir().parent))
                        list_dir.append(config.CORTX_ROOT_DIR)
                        list_dir.append(config.PRVSNR_DATA_SHARED_DIR)
                        DestroyNode.remove_dir(list_dir, [primary], setup_type)
                        DestroyNode.remove_pkgs(list_pkgs,
                                                [primary],
                                                setup_type)
            else:
                if state in (
                    "system.storage.glusterfs.teardown.volume_remove",
                    "provisioner.teardown",
                    "provisioner.passwordless_remove",
                    "system.storage.multipath.teardown"
                    "misc_pkgs.openldap.teardown",
                    "misc_pkgs.rabbitmq.teardown"
                ):
                    if state == 'provisioner.passwordless_remove':
                        list_dir = []
                        list_dir.append(str(config.profile_base_dir().parent))
                        # list_dir.append(config.CORTX_ROOT_DIR)
                        DestroyNode.remove_dir(list_dir,
                                               secondaries,
                                               setup_type)
                        DestroyNode.remove_dir(list_dir, [primary], setup_type)

                    logger.info(f"Applying '{state}' on {secondaries}")
                    # Execute first on secondaries then on primary.
                    self._apply_states(state, '|'.join(secondaries))

                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                    if state == 'provisioner.passwordless_remove':
                        list_pkgs = ["salt", "salt-minion", "salt-master"]
                        # TODO hack to remove salt using suboricess
                        DestroyNode.remove_pkgs(list_pkgs,
                                                [primary],
                                                SetupType.SINGLE)

                elif state in (
                    "ha.corosync-pacemaker.teardown",
                    "ha.cortx-ha.teardown",
                    "sspl.teardown"
                ):
                    logger.info(f"Applying '{state}' on {primary}")
                    self._apply_states(state, primary)

                    logger.info(f"Applying '{state}' on {secondaries}")
                    # Execute first on secondaries then on primary.
                    self._apply_states(state, '|'.join(secondaries))

                elif state in (
                    "provisioner.salt.teardown.package_remove"
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
        if not self._is_hw():
            raise errors.ProvisionerError(
                "The command is specifically for HW teardown. "
            )
        logger.info(f"Copy salt ssh config to {temp_dir}")
        salt_ssh_config = str(
            config.PRVSNR_FACTORY_PROFILE_DIR / 'srv/config'
        )

        run_subprocess_cmd(f"cp -rf {salt_ssh_config} {str(temp_dir)}")

        salt_config_master = str(
            temp_dir / 'config/master'
        )

        roster = str(
            temp_dir / 'config/roster'
        )

        ssh_client = DestroyNode._create_ssh_client(salt_config_master, roster)

        self.setup_ctx = SetupCtx(ssh_client)
        if run_args.states is None:  # all states
            self._run_states('ha', run_args)
            self._run_states('controlpath', run_args)
            self._run_states('iopath', run_args)
            self._run_states('prereq', run_args)
            self._run_states('system', run_args)
            self._run_states('bootstrap', run_args)

        else:
            if 'bootstrap' in run_args.states:
                logger.info("Teardown Provisioner Bootstrapped Environment")
                self._run_states('bootstrap', run_args)
            if 'system' in run_args.states:
                logger.info("Teardown the system states")
                self._run_states('system', run_args)

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

        logger.info(f"Remove salt ssh config from tmp")
        run_subprocess_cmd(f"rm -rf {str(temp_dir)}")

        logger.info("Destroy VM - Done")
        return run_args
