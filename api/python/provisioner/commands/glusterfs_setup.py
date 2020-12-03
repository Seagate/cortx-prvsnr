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

from typing import List, Dict, Type, Optional, Iterable
# import socket
import logging
import uuid
from pathlib import Path

from .. import (
    inputs,
    config,
    profile,
    utils
)
from ..vendor import attr
from ..errors import (
    ProvisionerError,
    SaltCmdResultError,
    SaltCmdRunError
)
from ..config import (
    ALL_MINIONS,
)
from ..pillar import PillarUpdater
# TODO IMPROVE EOS-8473
from ..utils import (
    load_yaml,
    dump_yaml,
    load_yaml_str,
    repo_tgz,
    run_subprocess_cmd,
    node_hostname_validator
)
from ..ssh import keygen
from ..salt import SaltSSHClient

from . import (
    CommandParserFillerMixin
)
from .setup_provisioner import (
    NodeGrains, Node, SetupCmdBase,
    SetupCtx, RunArgsSetupProvisionerGeneric
)


logger = logging.getLogger(__name__)

@attr.s(auto_attribs=True)
class RunArgsGlusterFSSetup:
    peers: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: 'glusterfs/peers'
        },
        converter=(
            lambda specs: [
                (s if isinstance(s, Node) else Node.from_spec(s))
                for s in specs
            ]
        )
    )
    in_docker: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: 'glusterfs/in_docker'
        },
        default=False
    )
    add_repo: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: 'glusterfs/add_repo'
        },
        default=False
    )
    cleanup: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: 'glusterfs/clieanup'
        },
        default=False
    )

@attr.s(auto_attribs=True)
class Runner:
    run_args: RunArgsSetupProvisionerGeneric

    ssh_client: SaltSSHClient = attr.ib(init=False, default=None)
    pillar_path: PillarPath = attr.ib(init=False, default=None)
    pillar: Dict = attr.ib(init=False, default=None)
    targets: List = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        self.ssh_client = SaltSSHClient()
        self.pillar_path = USER_SHARED_PILLAR
        self.pillar = self._prepare_pillar()
        self.targets = self.ssh_client.roster_targets()

    def _prepare_pillar(self):
        volumes = {
            'volume_salt_cache_jobs': {
                'export_dir': str(config.GLUSTERFS_VOLUME_SALT_JOBS),
                'mount_dir': '/var/cache/salt/master/jobs'
            },
            'volume_prvsnr_data': {
                'export_dir': str(config.GLUSTERFS_VOLUME_PRVSNR_DATA),
                'mount_dir': str(config.PRVSNR_DATA_SHARED_DIR)
            }
        }

        return dict(glusterfs={
            'in_docker': self.run_args.in_docker,
            'add_repo': self.run_args.add_repo,
            'volumes': volumes,
            'dirs': [
                vdata['export_dir'] for vdata in volumes.values()
            ],
            'peers': [
                peer for peer in self.run_args.peers
            ],
            'volumes': {
                vname: {
                    peer: vdata['export_dir']
                    for peer in self.run_args.peers
                } for vname, vdata in volumes.items()
            },
            'mounts': [
                (
                    # Note. as explaind in glusterfs docs the server here
                    # 'is only used to fetch the glusterfs configuration'
                    peers[0],     # TODO ??? remote

                    # each client assumes locally
                    # availble healthy glusterfs server
                    # 'localhost',

                    vname,
                    vdata['mount_dir']
                ) for vname, vdata in volumes.items()
            ]
        })

    def _cleanup(self):
        logger.info("Resolving glusterfs peer status")
        peer_status = ssh_client.run(
            'glusterfs.peer_status', targets=self.targets[0]
        )[self.targets[0]]


        logger.info("Resolving glusterfs volume info")
        volume_info = ssh_client.run(
            'glusterfs.info', targets=self.targets[0]
        )[self.targets[0]]

        # NOTE
        # - we definitely need to stop salt-master since his jobs
        #   mounts would be lost for some time
        # - salt-minion stop might be not necessary though
        # - stopping salt-master first to drop all new requests
        #   for salt jobs
        #   TODO move either to optional step or outside gluster at all
        try:
            logger.info(f"Stopping 'salt-master' service")
            ssh_client.state_single(
                "service.dead", fun_args=['salt-master']
            )
        except SaltCmdRunError as exc:  # TODO DRY
            if 'Stream is closed' in str(exc):
                logger.warning(
                    "Ensuring salt-master was stopped "
                    "(salt-ssh lost a connection)"
                )
                ssh_client.run(
                    'cmd.run', fun_args=['systemctl stop salt-master']
                )

        logger.info(f"Stopping 'salt-minion' service")
        ssh_client.state_single(
            "service.dead", fun_args=['salt-mininon']
        )

        # TODO move to teardown states
        logger.info("Stopping 'glusterfssharedstorage' service")
        ssh_client.state_single(
            "service.dead",
            fun_args=['glusterfssharedstorage.service']
        )

        logger.info(f"Removing glusterfs mounts")
        for _, _, mount_dir in self.pillar['mounts']:
            logger.debug(f"Removing mount {mount_dir}")
            ssh_client.state_single(
                'mount.unmounted',
                fun_kwargs={
                    'name': mount_dir,
                    'persist': True
                }
            )

        logger.info(f"Removing glusterfs bricks")
        for v_name, v_data in volume_info.items():
            # TODO EOS-14076 IMPROVE v_data also has replica info,
            #      need explore glusterfs more for better logic
            replicas_num = len(v_data['bricks'])
            for brick in v_data['bricks'].values():
                replicas_num -= 1
                logger.debug(
                    f"Removing brick {brick['path']} "
                    "from glusterfs volume {v_name}"
                )
                ssh_client.cmd_run(
                    (
                        f"echo y | gluster volume remove-brick "
                        f"{v_name} replica {replicas_num} "
                        f"{brick['path']} force"
                    ),
                    fun_kwargs=dict(python_shell=True),
                    targets=self.targets[0]
                )

        logger.info(f"Removing glusterfs peers")
        for peer in peer_status:
            logger.info(f"Removing glusterfs peer {peer}")
            # TODO ??? is 'force' necessary here
            ssh_client.cmd_run(
                f"echo y | gluster peer detach {peer} force",
                fun_kwargs=dict(python_shell=True),
                targets=self.targets[0]
            )

        logger.info(f"Removing glusterfs volumes")
        for v_name in volume_info:
            logger.debug(f"Removing glusterfs volume {v_name}")
            ssh_client.run(
                'glusterfs.delete_volume',
                fun_args=[v_name],
                fun_kwargs=dict(stop=True),
                targets=self.targets[0]
            )

    def _install(self):
        if glusterfs_pillar['in_docker']:
            # Note. there is an issue in salt-ssh
            # https://github.com/saltstack-formulas/docker-formula/issues/234  # noqa: E501
            # so we have to apply docker using on-server salt
            logger.info("Installing Docker")
            ssh_client.cmd_run(
                "salt-call --local state.apply components.misc_pkgs.docker"
            )

        logger.info("Installing glusterfs servers")
        # TODO IMPROVE ??? EOS-9581 glusterfs docs complains regarding /srv
        #      https://docs.gluster.org/en/latest/Administrator%20Guide/Brick%20Naming%20Conventions/  # noqa: E501
        ssh_client.state_apply(
            'glusterfs.server.install',
            fun_kwargs={
                'pillar': self.pillar
            }
        )

        logger.info("Installing glusterfs clients")
        # should be run only on one node
        ssh_client.state_apply(
            'glusterfs.client.install',
            fun_kwargs={
                'pillar': self.pillar
            }
        )


    def _config(self):
        logger.info("Configuring glusterfs servers")
        # TODO IMPROVE ??? EOS-9581 glusterfs docs complains regarding /srv
        #      https://docs.gluster.org/en/latest/Administrator%20Guide/Brick%20Naming%20Conventions/  # noqa: E501
        ssh_client.state_apply(
            'glusterfs.server',
            fun_kwargs={
                'pillar': self.pillar
            }
        )

        logger.info("Configuring glusterfs cluster")
        # should be run only on one node
        ssh_client.state_apply(
            'glusterfs.cluster',
            targets=self.targets[0],
            fun_kwargs={
                'pillar': self.pillar
            }
        )

        logger.info("Configuring glusterfs clients")
        # should be run only on one node
        ssh_client.state_apply(
            'glusterfs.client',
            fun_kwargs={
                'pillar': self.pillar
            }
        )

    def run(self):
        salt_logger = logging.getLogger('salt.fileclient')
        salt_logger.setLevel(logging.WARNING)

        logger.debug(f"glusterfs pillar: {self.pillar}")

        logger.info("Installing glusterfs pkgs")
        self._install()

        if self.run_args.cleanup:
            logger.info("Resetting current glusterfs configuration")
            self._cleanup()

        logger.info("Configuring glusterfs")
        self._config()

        # now we should have proviisoner shared pillar availble,
        # so dump glusterfs pillar there
        pi_updater = PillarUpdater(pillar_path=self.pillar_path)
        pi_updater.update(('glusterfs', pillar))
        pi_updater.apply()



@attr.s(auto_attribs=True)
class GlusterFSSetup(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsGlusterFSSetup

    def run(self, *args, **kwargs):
        run_args = RunArgsGlusterFSSetup(*args, **kwargs)
        runner = Runner(run_args, profile)
        return runner.run()
