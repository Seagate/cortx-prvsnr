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
import json
import configparser

from typing import Type
from pathlib import Path

from .. import (
    inputs,
    config
)
from ..vendor import attr

from ..salt import cmd_run
from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsGenerateConfigAttrs:
    config_path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config.ini file path"
            }
        },
        default='/root/config.ini'
    )


@attr.s(auto_attribs=True)
class GenerateConfig(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsGenerateConfigAttrs
    description = "API to generate config.ini file from given params"

    def create_data(self, parent, data, configs, section):
        for x, y in data.items():
            if isinstance(y, dict):
                if 'local' not in x:
                    parent.append(x)
                self.create_data(parent, y, configs, section)
                if x in parent:
                    parent.remove(x)
            else:
                s = '.'.join(parent)
                s = f"{s}.{x}" if s else x
                if y:
                    y = ','.join(y) if isinstance(y, list) else str(y)
                else:
                    y = ''
                configs[section][s] = y

    def _get_local_data(self, key, config_path):
        node_key = 'cluster:srvnode-0'
        data = cmd_run(
                   f"salt-call --local pillar.get {node_key} --out=json",
                   targets=config.ALL_MINIONS
               )
        configs = configparser.ConfigParser()
        for key, value in data.items():
            configs[key] = {}
            self.create_data([], json.loads(value), configs, key)
        data = cmd_run(
                   "salt-call --local pillar.get cluster:mgmt_vip --out=json",
                   targets=config.LOCAL_MINION
               )
        configs['cluster'] = {}
        value = json.loads(data['srvnode-1'])
        configs['cluster']['mgmt_vip'] = value['local']
        with open(config_path, 'w') as configfile:
            configs.write(configfile)

    def run(self, **kwargs):

        if Path(kwargs['config_path']).is_file():
            logger.warn("Config file present, Updating config.ini file.")
        self._get_local_data('cluster', kwargs['config_path'])

        logger.info(f"Config file created {kwargs['config_path']}")
