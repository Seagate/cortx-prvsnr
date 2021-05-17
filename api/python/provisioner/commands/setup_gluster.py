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

from typing import List, Type, Optional
# import socket
import logging

from .. import (
    inputs,
    config
)
from ..vendor import attr
from ..errors import (
    SaltCmdRunError
)
from ..config import (
    ALL_MINIONS
)
from ..pillar import PillarUpdater
# TODO IMPROVE EOS-8473
from ..utils import (
    dump_yaml,
    load_yaml
)
from .bootstrap_provisioner import (
    RunArgsSetupProvisionerGeneric,
    SetupCmdBase,
    SetupCtx
)
from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)

add_pillar_merge_prefix = PillarUpdater.add_merge_prefix


@attr.s(auto_attribs=True)
class SetupGluster(SetupCmdBase, CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSetupProvisionerGeneric
    nodes: Optional[List] = None
    setup_ctx: Optional[SetupCtx] = None

    def _prepare_glusterfs_pillar(self, profile_paths, in_docker=False):
        pillar_all_dir = profile_paths['salt_pillar_dir'] / 'groups/all'
        pillar_all_dir.mkdir(parents=True, exist_ok=True)

        glusterfs_pillar_path = pillar_all_dir / 'glusterfs.sls'
        if glusterfs_pillar_path.exists():
            data = load_yaml(glusterfs_pillar_path)['glusterfs']
        else:
            data = {
                'in_docker': in_docker,
                'volumes': {
                    'volume_salt_cache_jobs': {
                        'export_dir': str(config.GLUSTERFS_VOLUME_SALT_JOBS),
                        'mount_dir': '/var/cache/salt/master/jobs'
                    },
                    'volume_prvsnr_data': {
                        'export_dir': str(config.GLUSTERFS_VOLUME_PRVSNR_DATA),
                        'mount_dir': str(config.PRVSNR_DATA_SHARED_DIR)
                    }
                }
            }
            dump_yaml(glusterfs_pillar_path,  dict(glusterfs=data))

        return data

    def run(self, nodes, **kwargs):  # noqa: C901 FIXME
        run_args = RunArgsSetupProvisionerGeneric(nodes=nodes, **kwargs)
        if self.nodes:
            run_args.nodes = self.nodes
        salt_logger = logging.getLogger('salt.fileclient')
        salt_logger.setLevel(logging.WARNING)
        if self.setup_ctx:
            ssh_client = self.setup_ctx.ssh_client
        # generate setup name
        setup_location = self.setup_location(run_args)
        setup_name = self.setup_name(run_args)

        # PREPARE FILE & PILLAR ROOTS

        logger.info(f"Starting to build setup '{setup_name}'")

        paths = config.profile_paths(
            config.profile_base_dir(
                location=setup_location, setup_name=setup_name
            )
        )

        # TODO IMPROVE EOS-9581 not all masters support
        master_targets = (
            ALL_MINIONS if run_args.ha else run_args.primary.minion_id
        )

        # TODO glusterfs use usual pillar instead inline one
        glusterfs_pillar = self._prepare_glusterfs_pillar(
            paths, in_docker=run_args.glusterfs_docker
        )
        volumes = glusterfs_pillar['volumes']

        glusterfs_server_pillar = {
            'glusterfs_dirs': [
                vdata['export_dir'] for vdata in volumes.values()
             ]
        }
        logger.debug(
            f"glusterfs server pillar: {glusterfs_server_pillar}"
        )
        glusterfs_cluster_pillar = {
            'glusterfs_peers': [
                node.ping_addrs[0] for node in run_args.nodes
            ],
            'glusterfs_volumes': {
                vname: {
                    node.ping_addrs[0]: vdata['export_dir']
                    for node in run_args.nodes
                } for vname, vdata in volumes.items()
            }
        }
        logger.debug(
            f"glusterfs cluster pillar: {glusterfs_cluster_pillar}"
        )

        glusterfs_client_pillar = {
            'glusterfs_mounts': [
                (
                    # Note. as explaind in glusterfs docs the server here
                    # 'is only used to fetch the glusterfs configuration'
                    run_args.primary.ping_addrs[0],     # TODO ??? remote

                    # each client assumes locally
                    # availble healthy glusterfs server
                    # 'localhost',

                    vname,
                    vdata['mount_dir']
                ) for vname, vdata in volumes.items()
            ]
        }
        logger.debug(
            f"glusterfs client pillar: {glusterfs_client_pillar}"
        )
        # TODO IMPROVE !!!
        #       that should be applied only for replace-node
        #       logic and no here
        if run_args.field_setup:
            logger.info("Resolving glusterfs volume info")
            volume_info = ssh_client.run(
                'glusterfs.info',
                targets=run_args.primary.minion_id
            )[run_args.primary.minion_id]

            # NOTE
            # - we definitely need to stop salt-master since his jobs
            #   mounts would be lost for some time
            # - salt-minion stop might be not necessary though
            # - stopping salt-master first to drop all new requests
            #   for salt jobs
            try:
                logger.info("Stopping 'salt-master' service")
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

            logger.info("Stopping 'salt-minion' service")
            ssh_client.state_single(
                "service.dead", fun_args=['salt-mininon']
            )

            # TODO move to teardown states
            logger.info("Stopping 'glusterfssharedstorage' service")
            ssh_client.state_single(
                "service.dead",
                fun_args=['glusterfssharedstorage.service']
            )

            logger.info("Removing glusterfs mounts")
            for _, _, mount_dir in glusterfs_client_pillar[
                'glusterfs_mounts'
            ]:
                logger.debug(f"Removing mount {mount_dir}")
                ssh_client.state_single(
                    'mount.unmounted',
                    fun_kwargs={
                        'name': mount_dir,
                        'persist': True
                    }
                )

            secondaries = tuple([
                node.ping_addrs[0] for node in run_args.secondaries
            ])
            logger.info(
                f"Removing old nodes {secondaries} glusterfs bricks"
            )
            for v_name, v_data in volume_info.items():
                # TODO EOS-14076 IMPROVE v_data also has replica info,
                #      need explore glusterfs more for better logic
                replicas_num = len(v_data['bricks'])
                for brick in v_data['bricks'].values():
                    if brick['path'].startswith(secondaries):
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
                            targets=run_args.primary.minion_id
                        )

            for peer in secondaries:
                logger.info(f"Removing old node glusterfs peer {peer}")
                # TODO ??? is 'force' necessary here
                ssh_client.cmd_run(
                    f"echo y | gluster peer detach {peer} force",
                    fun_kwargs=dict(python_shell=True),
                    targets=run_args.primary.minion_id
                )

            logger.info("Removing old glusterfs volumes")
            for v_name in volumes:
                if v_name in volume_info:
                    logger.debug(f"Removing glusterfs volume {v_name}")
                    ssh_client.run(
                        'glusterfs.delete_volume',
                        fun_args=[v_name],
                        fun_kwargs=dict(stop=True),
                        targets=run_args.primary.minion_id
                    )

        if glusterfs_pillar['in_docker']:
            # Note. there is an issue in salt-ssh
            # https://github.com/saltstack-formulas/docker-formula/issues/234  # noqa: E501
            # so we have to apply docker using on-server salt
            logger.info("Installing Docker")
            ssh_client.cmd_run(
                "salt-call --local state.apply components.misc_pkgs.docker"
            )

        logger.info("Configuring glusterfs servers")
        # TODO IMPROVE ??? EOS-9581 glusterfs docs complains regarding /srv
        #      https://docs.gluster.org/en/latest/Administrator%20Guide/Brick%20Naming%20Conventions/  # noqa: E501
        ssh_client.state_apply(
            'glusterfs.server',
            targets=master_targets,
            fun_kwargs={
                'pillar': glusterfs_server_pillar
            }
        )

        logger.info("Configuring glusterfs cluster")
        # should be run only on one node
        ssh_client.state_apply(
            'glusterfs.cluster',
            targets=run_args.primary.minion_id,
            fun_kwargs={
                'pillar': glusterfs_cluster_pillar
            }
        )

        logger.info("Configuring glusterfs clients")
        # should be run only on one node
        ssh_client.state_apply(
            'glusterfs.client',
            fun_kwargs={
                'pillar': glusterfs_client_pillar
            }
        )
