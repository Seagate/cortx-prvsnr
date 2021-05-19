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

import errno
import os
import sys
import json
import salt.client
from pathlib import Path

if "2." in sys.version:
  from ConfigParser import ConfigParser, ParsingError, MissingSectionHeaderError
else:
  from configparser import ConfigParser, ParsingError, MissingSectionHeaderError
from shutil import copyfile

import commons

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules
# salt-call sspl.merge_health_map_schema "/tmp/resource_health_view.json"


def merge_health_map_schema(source_json="/tmp/resource_health_view.json"):

  local = salt.client.LocalClient()
  __pillar__ = getattr(sys.modules[__name__], '__pillar__')
  healthmap_schema_pillar = __pillar__['commons']['health_map_schema']
  health_map_path = healthmap_schema_pillar['path']
  health_map_file = healthmap_schema_pillar['filename']

  data = local.cmd('*', 'file.read', [source_json])
  node_data = []
  for node in __pillar__['cluster'].keys():
    if "srvnode-" in node:
      node_data.append(json.loads(data[node]))

  node_rack_nodes = None
  for i, _data in enumerate(node_data):
    if i == 0:
      node_rack_nodes = (
        _data["cluster"]["sites"]["001"]["rack"]["001"]["nodes"]
      )
    else:
      node_rack_nodes.update(
        _data["cluster"]["sites"]["001"]["rack"]["001"]["nodes"]
      )

  local.cmd('*', 'file.mkdir',[health_map_path])
  local.cmd(
    '*',
    'file.write',
    [os.path.join(health_map_path, health_map_file), json.dumps(node_rack_nodes, indent=4)]
  )

  # TODO use salt formulas, CSM suggested to have 777 permission just for hotfix
  local.cmd(
    '*',
    'cmd.run',
    ['chmod 777 {}'.format(os.path.join(health_map_path, health_map_file))]
  )

  return True
