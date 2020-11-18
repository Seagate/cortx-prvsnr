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

# import logging
#
# from ..ssh import keygen
#
# logger = logging.getLogger(__name__)
#
#
# @attr.s(auto_attribs=True)
# class SSHResource(Resource):
#     name = 'salt-master'
#
#
# class SSHResourceSLS(ResourceCortxSLS):
#     resource = SSHResource
#
#
# @attr.s(auto_attribs=True)
# class Config(SSHResourceSLS):
#     name = 'config'
#     state_name = 'ssh.config'
#
#     nodes: Union[List[Node], _PrvsnrValue] = attr_ib(
#         default=UNCHANGED
#     )
#     # regenerate: bool = attr.ib(
#     #     metadata={
#     #         inputs.METADATA_ARGPARSER: {
#     #             'help': (
#     #                 "Regenerate keys even if already exist"
#     #             ),
#     #         }
#     #     },
#     #     default=False
#     # )
#
#     def _gen_keys(self, targets):
#         ssh_dir = self.fileroot_path("ssh/files")
#         key_pem = ssh_dir / SSH_PRIV_KEY.name
#         key_pub = ssh_dir / SSH_PUB_KEY.name
#
#         # XXX validation that these paths are not dirs
#         if not (key_pem.exists() and key_pub.exists()):  # or regenerate
#             # FIXME violates FileRoot encapsulation, better way:
#             # - generate in some temp location
#             # - copy to fileroot
#             if key_pem.is_file():
#                 key_pem.unlink()
#             if key_pub.is_file():
#                 key_pub.unlink()
#
#             logger.info('Generating setup keys')
#             keygen(key_pem)
#         else:
#             logger.info('Generating setup keys [skipped]')
#
#         key_pem.chmod(0o600)
#
#     def _gen_ssh_spec(self):
#         ssh_spec_pi_key = 'ssh/spec'
#
#         if self.nodes is UNCHANGED:
#             # validate that ssh spec exists
#             pillar_spec = self.salt_client.pillar_get(
#                 ssh_spec_pi_key, local_minion_id
#             )
#
#             if not pillar_spec:
#                 raise ValueError('no ssh spec in pillar')
#             else:
#                 return
#
#         ssh_spec = {
#             node.minion_id: {
#                 'host': [
#                     node.minion_id,
#                     node.ping_addrs[0]
#                 ],
#                 # XXX ssh might need other endpoint
#                 'hostname': node.ping_addrs[0],
#                 'port': node.port,
#                 # XXX hard coded
#                 'user': 'root',
#             }
#             for node in self.nodes
#         }
#
#         salt_client.pillar_set([(ssh_spec_pi_key, ssh_spec)])
#
#     def setup_roots(self):
#         self._gen_keys()
#         self._gen_ssh_spec()
#
#
# @attr.s(auto_attribs=True)
# class Check(SSHResourceSLS):
#     name = 'check'
#     state_name = 'ssh.check'
