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

import json
from cortx_setup.commands.common_utils import get_pillar_data

from ..command import Command


class ResourceShow(Command):

    def resource_filter_status(self, resource_state, resource_map):
        if isinstance(resource_map, dict):
            for key in resource_map.keys():
                resource_map[key] = self.resource_filter_status(
                    resource_state, resource_map[key])
            return resource_map
        elif isinstance(resource_map, list):
            temp = []
            for i, _ in enumerate(resource_map):
                if "health" in resource_map[i].keys():
                    if resource_state in resource_map[i]['health']['status']:
                        temp.append(resource_map[i])
            return temp
        else:
            return resource_map


    def parse_resource_file(self, resource_map_path: str):
        file_type, file_path=resource_map_path.split("://")
        if "json" in file_type:
            with open(file_path, "r") as f:
                return json.loads(f.read())
        else:
            raise Exception(f"Unsupported file type {file_type}")

    def filter_resource_type(self, resource_type, resource_dict):
        key_list = resource_type.split('>')
        for key in key_list:
            if "[" in key:
                index = key[key.find("[")+1:key.find("]")]
                key = key[:key.find("[")]
                if index.isdigit():
                    index=int(index)
                resource_dict = resource_dict[key][index]
            else:        
                resource_dict=resource_dict[key]
        return resource_dict



    _args={
        'manifest': {
            'action': 'store_true',
            'optional': True,
            'help': 'discover HW/SW Manifest for all resources'
        },
        'health': {
            'action': 'store_true',
            'optional': True,
            'help': 'Health check for all the resources in the system'
        },
        'resource_type': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Resource type for which resource map is to be fetched e.g node.compute.0.hw.disks or node.compute.0.hw'
        },
        'resource_state': {
            'type': str,
            'default': None,
            'optional': True,
            'choices': ['OK', 'FAULT', 'DEGRADED'],
            'help': 'The current state of the resources'
        },
    }

    def run(self, **kwargs):

        if kwargs["health"]:
            # get resource_map
            # resource_map_path =
            # ResourceDiscover.get_resource_map(resource_type =
            # kwargs['resource_type'])
            resource_map_path = get_pillar_data(
                'provisioner/common_config/resource_map_path')
            resource_dict=self.parse_resource_file(resource_map_path)
            resource_dict=self.filter_resource_type(
                kwargs['resource_type'], resource_dict)

            if kwargs['resource_state']:
                resource_dict=self.resource_filter_status(
                    kwargs['resource_state'], resource_dict)

            self.logger.info(json.dumps(resource_dict, indent=4))
            # return json.dumps(resource_dict, indent=4)

        else:
            self.logger.debug("discover HW/SW Manifest for all resources")
        self.logger.debug("Done")
