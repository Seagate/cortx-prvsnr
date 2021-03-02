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
# class SetupRoster(ComponentBase):
#     name = 'roster'
#
#     nodes: List[Node] = attr_ib('nodes', cli_spec='roster/nodes')
#     priv_key: Path = attr_ib(
#         'path_exists',
#         default=config.SSH_PRIV_KEY,
#         cli_spec='roster/priv_key'
#     )
#     roster_file: Path = attr_ib(
#         'path',
#         default=config.SALT_ROSTER_DEFAULT,
#         cli_spec='roster/path'
#     )
#
#     @staticmethod
#     def build(self, nodes: List[Node], priv_key):
#         return {
#             node.minion_id: {
#                 'host': node.host,
#                 'user': node.user,
#                 'port': node.port,
#                 'priv': str(priv_key)
#             } for node in nodes
#         }
#
#     def run(self):
#         dump_yaml(
#             self.roster_file, self.build(self.nodes, self.priv_key)
#         )
