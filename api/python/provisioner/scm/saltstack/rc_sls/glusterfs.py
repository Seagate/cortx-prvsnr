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

# from abc import ABC, abstractmethod
# from typing import Type
# import logging
# import argparse
# import uuid
#
# from ..vendor import attr
# from .. import (
#     inputs
# )
# from ..cli_parser import KeyValueListAction
# from ..attr_gen import attr_ib
# from .glusterfs_setup import (
#     RunArgsGlusterFSSetup,
#     Runner as GlusterFSSetupRunner
# )
#
# from . import (
#     CommandParserFillerMixin
# )
#
#
# logger = logging.getLogger(__name__)
# _mod = sys.modules[__name__]
#
#
# @attr.s(auto_attribs=True)
# class GlusterFSPrepareMixin:
#     name = 'prepare'
#     sls = 'glusterfs.prepare_new'
#
#     add_repo: bool = attr.ib(
#         metadata={
#             inputs.METADATA_ARGPARSER: 'glusterfs/add_repo'
#         },
#         default=False
#     )
#
#     def setup_roots(self):
#         # XXX what if mixin is applied twice
#         #     as both a client and a peer
#         pillar = dict(glusterfs=dict(common={
#             'add_repo': self.add_repo,
#         )})
#
#         salt_client.pillar_set(_pillar)
#
#
# @attr.s(auto_attribs=True)
# class GlusterFSPeer(Resource):
#     name = 'glusterfs-peer'
#
#
# class GlusterFSPeerSLS(Resource3rdPartySLS):
#     resource_t = GlusterFSPeer
#
#
# class Prepare(GlusterFSPeerSLS, GlusterFSPrepareMixin):
#     pass
#
#
# @attr.s(auto_attribs=True)
# class Install(GlusterFSPeerSLS):
#     name = 'install'
#     sls = 'glusterfs.server.install_new'
#
#     in_docker: bool = attr.ib(
#         metadata={
#             inputs.METADATA_ARGPARSER: 'glusterfs/in_docker'
#         },
#         default=False
#     )
#
#     def setup_roots(self):
#         pillar = dict(glusterfs=dict(servers={
#             'in_docker': self.in_docker
#             }))
#
#         salt_client.pillar_set(_pillar)
#
#     def _run(self, targets):
#
#         if self.in_docker:
#             # Note. there is an issue in salt-ssh
#             # https://github.com/saltstack-formulas/docker-formula/issues/234  # noqa: E501
#             # so we have to apply docker using on-server salt
#             logger.info("Installing Docker")
#             self.client.cmd_run(
#                 "salt-call --local state.apply components.misc_pkgs.docker"
#             )
#
#         return super().run(targets)
#
#
# @attr.s(auto_attribs=True)
# class GlusterFSCluster(Resource):
#     name = 'glusterfs-cluster'
#
#
# class GlusterFSClusterSLS(Resource3rdPartySLS):
#     resource_t = GlusterFSCluster
#
#
# # should be run only on one node
# @attr.s(auto_attribs=True)
# class Config(GlusterFSClusterSLS):
#     name = 'config'
#     sls = 'glusterfs.cluster.config_new'
#
#     def setup_roots(self):
#         volumes = {
#             config.GLUSTERFS_VOLUME_NAME_SALT_JOBS: (
#                 str(config.GLUSTERFS_VOLUME_SALT_JOBS)
#             ),
#             config.GLUSTERFS_VOLUME_NAME_PRVSNR_DATA: (
#                 str(config.GLUSTERFS_VOLUME_PRVSNR_DATA)
#             )
#         }
#
#         _pillar = dict(glusterfs=dict(cluster={
#             'peers': [peer for peer in self.run_args.peers],
#             'volumes': volumes
#             }))
#
#         salt_client.pillar_set(_pillar)
#
#
# @attr.s(auto_attribs=True)
# class Teardown(GlusterFSClusterSLS):
#     name = 'teardown'
#     sls = 'glusterfs.cluster.teardown'
#
#     # XXX move to sls
#     def _run(self, targets):
#         logger.info("Resolving glusterfs volume info")
#         volume_info = self.client.run(
#             'glusterfs.info',
#             targets=run_args.primary.minion_id
#         )[run_args.primary.minion_id]
#
#         _pillar = dict(glusterfs={
#             'peers': [peer for peer in self.run_args.peers],
#             'volumes': volumes
#         })
#
#         pillar = self.client.pillar_get('glusterfs:cluster')
#         peers = pillar['peers']
#         volumes = pillar['volumes']
#
#         # XXX violation from a legacy logic: all peers instead of secondaries
#         logger.info(
#             f"Removing peers {peers} glusterfs bricks"
#         )
#         for v_name, v_data in volume_info.items():
#             # TODO EOS-14076 IMPROVE v_data also has replica info,
#             #      need explore glusterfs more for better logic
#             replicas_num = len(v_data['bricks'])
#             for brick in v_data['bricks'].values():
#                 if brick['path'].startswith(peers):
#                     replicas_num -= 1
#                     logger.debug(
#                         f"Removing brick {brick['path']} "
#                         "from glusterfs volume {v_name}"
#                     )
#                     self.client.cmd_run(
#                         (
#                             f"echo y | gluster volume remove-brick "
#                             f"{v_name} replica {replicas_num} "
#                             f"{brick['path']} force"
#                         ),
#                         fun_kwargs=dict(python_shell=True),
#                         # XXX
#                         targets=run_args.primary.minion_id
#                     )
#
#         for peer in peers:
#             logger.info(f"Removing old node glusterfs peer {peer}")
#             # TODO ??? is 'force' necessary here
#             self.client.cmd_run(
#                 f"echo y | gluster peer detach {peer} force",
#                 fun_kwargs=dict(python_shell=True),
#                 # XXX
#                 targets=run_args.primary.minion_id
#             )
#
#         logger.info(f"Removing glusterfs volumes")
#         for v_name in volumes:
#             if v_name in volume_info:
#                 logger.debug(f"Removing glusterfs volume {v_name}")
#                 self.client.run(
#                     'glusterfs.delete_volume',
#                     fun_args=[v_name],
#                     fun_kwargs=dict(stop=True),
#                     # XXX
#                     targets=run_args.primary.minion_id
#                 )
#
#
#
# @attr.s(auto_attribs=True)
# class GlusterFSClient(Resource):
#     name = 'glusterfs-client'
#
#
# class GlusterFSClientSLS(Resource3rdPartySLS):
#     resource_t = GlusterFSClient
#
#
# class Prepare(GlusterFSClientSLS, GlusterFSPrepareMixin):
#     pass
#
#
# @attr.s(auto_attribs=True)
# class Install(GlusterFSClientSLS):
#     name = 'install'
#     sls = 'glusterfs.client.install_new'
#
#
#
# @attr.s(auto_attribs=True)
# class Config(GlusterFSClientSLS):
#     name = 'config'
#     sls = 'glusterfs.client.config_new'
#
#     mount_server: str
#
#     def setup_roots(self):
#         mounts = {
#             config.GLUSTERFS_VOLUME_NAME_SALT_JOBS: (
#                 str(config.SALT_JOBS_CACHE_DIR)
#             ),
#             config.GLUSTERFS_VOLUME_NAME_PRVSNR_DATA: (
#                 str(config.PRVSNR_DATA_SHARED_DIR)
#             )
#         }
#
#         _pillar = dict(glusterfs=dict(clients={
#             # TODO DOC
#             #  Note. as explaind in glusterfs docs
#             # (https://docs.gluster.org/en/latest/Administrator-Guide/Setting-Up-Clients/#manual-mount)
#             #  the server here 'is only used to fetch the glusterfs
#             #  configuration' and then client will reach all other servers
#             #  that are configured for a volume, so HA will take place at
#             #  runtime but at mount time that server should be reachable
#             'mount_server': self.mount_server,
#             'mounts': mounts
#         }))
#
#         salt_client.pillar_set(_pillar)
#
#
# @attr.s(auto_attribs=True)
# class Disconnect(GlusterFSClientSLS):
#     name = 'disconnect'
#
#     # XXX move to sls
#     def _run(self, targets):
#         pillar = self.client.pillar_get('glusterfs:client')
#         mounts = pillar['mounts']
#
#         # TODO move to teardown states
#         logger.info("Stopping 'glusterfssharedstorage' service")
#         self.client.state_single(
#             "service.dead",
#             fun_args=['glusterfssharedstorage.service']
#         )
#
#         logger.info(f"Removing glusterfs mounts")
#         for mount_dir in mounts.values():
#             logger.debug(f"Removing mount {mount_dir}")
#             self.client.state_single(
#                 'mount.unmounted',
#                 fun_kwargs={
#                     'name': mount_dir,
#                     # XXX check that it's ok for a container environment
#                     'persist': True
#                 }
#             )
