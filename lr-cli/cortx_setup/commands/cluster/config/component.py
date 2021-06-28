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
#
# Cortx Setup API to execute complete cluster config


from typing import List, Optional

from cortx_setup.commands.command import Command
from cortx_setup.commands.common_utils import (
    get_provisioner_states,
    get_cortx_states
)

from provisioner.commands import deploy


class ClusterConfigComponent(Command):

    _args = {
        'type': {
            'type': str,
            'optional': True,
            'default': None,
            'dest': 'component_group',
            'choices': ['prerequisites', 'foundation', 'iopath', 'controlpath', 'ha'],
            'help': 'Component group to deploy'
        }
    }

    def _configure(self, components: List, stages: Optional[List] = None):
        for component in components:
            self.logger.debug(f"Applying components.{component} on nodes")
            try:
                deploy.Deploy()._apply_state(
                    f"components.{component}",
                    stages=stages if stages else None
                )
            except Exception as exc:
                raise exc

    def run(self, component_group):
        """
        cortx cluster config command

        Deploy system

        Execution:
        `cortx_setup cluster config component --type <state>`

        """
        try:
            # Getting provisioner states for deployment
            noncortx_components = get_provisioner_states()
            cortx_components = get_cortx_states()

            if component_group is None:
                self.logger.debug(f"Deploying prerequisites components on nodes")
                self._configure(
                    noncortx_components['prerequisites']
                )
                for component_group in cortx_components:
                    self.logger.debug(f"Deploying {component_group} components on nodes")
                    self._configure(
                        cortx_components[component_group],
                        stages=['config.config', 'config.init_mod']
                    )
                self.logger.debug(f"Deploying ha components on nodes")
                self._configure(
                    ['ha.cortx-ha'],
                    stages=[
                        'config.post_install','config.prepare',
                        'config.config', 'config.init_mod']
                )
            elif component_group in noncortx_components:
                self.logger.debug(f"Deploying prerequisites components on nodes")
                self._configure(
                    noncortx_components['prerequisites']
                )
            elif component_group in cortx_components:
                self.logger.debug(f"Deploying {component_group} components on nodes")
                self._configure(
                    cortx_components[component_group],
                    stages=['config.config', 'config.init_mod']
                )
            elif component_group == 'ha':
                self.logger.debug(f"Deploying cortx ha components on nodes")
                self._configure(
                    ['ha.cortx-ha'],
                    stages=[
                        'config.post_install','config.prepare',
                        'config.config', 'config.init_mod']
                )
            self.logger.debug(f"Deployment done")
        except ValueError as exc:
            raise ValueError(
              f"Cluster Config Failed. Reason: {str(exc)}"
            )
