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

# Cortx Setup API for configuring cortx

from typing import List, Optional
from cortx_setup.commands.command import Command
from provisioner.commands import deploy
from provisioner.salt import local_minion_id
from cortx_setup.commands.common_utils import (
    get_provisioner_states,
    get_cortx_states
)

node_id = local_minion_id()


class ClusterConfigComponent(Command):
    _args = {
        'type': {
            'type': str,
            'optional': True,
            'default': None,
            'dest': 'component_group',
            'choices': ['foundation', 'iopath', 'controlpath', 'ha'],
            'help': 'Component group'
        }
    }

    def _configure(self, components: List, stages: Optional[List] = None):
        for component in components:
            self.logger.info(f"Applying components.{component} on nodes")
            try:
                deploy.Deploy()._apply_state(
                    f"components.{component}",
                    stages=stages if stages else None
                )
            except Exception as ex:
                raise ex

    def run(self, component_group: str = None):
        """
        Cortx cluster config command

        Deploy system, prereqs and cortx components

        Execution:
        `cortx_setup cluster config component --type <component_group>`

        """

        noncortx_components = get_provisioner_states()
        cortx_components = get_cortx_states()

        # Deploy system, prereqs and cortx components
        if component_group is None:
            for component_group in noncortx_components:
                self.logger.info(
                    f"Deploying {component_group} components on nodes")
                self._configure(
                    noncortx_components[component_group]
                )
        elif component_group in cortx_components:
            self.logger.info(
                f"Deploying {component_group} components on nodes")
            self._configure(
                cortx_components[component_group],
                stages=['config.config', 'config.init_mod']
            )
