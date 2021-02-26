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

# Python API to generate roster file required for salt-ssh
import logging
from typing import Type
from pathlib import Path

from ..utils import dump_yaml
from .. import (
    inputs,
    config,
    values
)
from ..vendor import attr

from ..pillar import PillarKey, PillarResolver

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsGenerateRosterAttrs:
    roster_path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "roster file path"
            }
        },
        default=str(config.PRVSNR_FACTORY_PROFILE_DIR / 'srv/roster')
    )
    user: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "user for salt-ssh"
            }
        },
        default='root'
    )
    port: int = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "port for salt-ssh"
            }
        },
        converter=int,
        default=22
    )
    priv_key: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "private key path for salt-ssh"
            }
        },
        default=str(config.PRVSNR_FACTORY_PROFILE_DIR / '.ssh/setup.id_rsa')
    )


@attr.s(auto_attribs=True)
class GenerateRoster(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsGenerateRosterAttrs
    _description = "API to generate roster file from given params"

    def _get_pillar_data(self, key):
        """Retrieve pillar data."""
        pillar_key = PillarKey(key)
        pillar = PillarResolver(config.LOCAL_MINION).get([pillar_key])
        pillar = next(iter(pillar.values()))
        if not pillar[pillar_key] or pillar[pillar_key] is values.MISSED:
            raise ValueError(f"value is not specified for {key}")
        else:
            return pillar[pillar_key]

    def _get_nodes_list(self):
        """Retrieve node  list from pillar"""
        nodes = []
        for key in self._get_pillar_data("cluster"):
            if 'srvnode' in key:
                nodes.append(key)
        return nodes

    def _get_node_host_map(self):
        """Provide map of node and hostname"""
        host_node_map = {}
        for node in self._get_nodes_list():
            host = self._get_pillar_data(
                       f'cluster/{node}/hostname')
            host_node_map.update({node: host})
        return host_node_map

    def _prepare_roster(
        self, nodes: dict, **kwargs
    ):
        roster = {
            node_id: {
                'host': host,
                'user': kwargs['user'],
                'port': kwargs['port'],
                'priv': str(kwargs['priv_key']),
                'minion_opts': {
                    'use_superseded': ['module.run']
                }
            } for node_id, host in nodes.items()
        }
        dump_yaml(kwargs['roster_path'], roster)

    def run(self, **kwargs):

        if Path(kwargs['roster_path']).is_file():
            logger.warn("Roster file present, Updating roster file.")

        if not Path(kwargs['priv_key']).is_file():
            raise ValueError('Private key not present')

        host_node_map = self._get_node_host_map()
        self._prepare_roster(host_node_map, **kwargs)
        logger.info(f"Roster file created {kwargs['roster_path']}")
