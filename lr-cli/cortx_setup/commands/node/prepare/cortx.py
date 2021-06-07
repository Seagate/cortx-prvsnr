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

from cortx_setup.commands.command import Command
from provisioner.commands import deploy
from provisioner.salt import (
    local_minion_id
)
from cortx_setup.commands.common_utils import (
    get_provisioner_states,
    get_cortx_states
)

node_id = local_minion_id()

provisioner_components = get_provisioner_states()

cortx_components = get_cortx_states()


class NodePrepare(Command):
    """Cortx Setup API for preparing node"""
    _args = {}
    
    # deploy the specific component states wrt to stages like prepare, config, post_install
    def _deploy(self, components: dict, stage: str = None):
        for component in components:
            states = components[component]
            for state in states:
                if stage and component not in ['platform', '3rd_party']:
                    state = f"{state}.{stage}"

                try:
                    self.logger.debug(
                        f"Running {state} for {node_id}"
                    )
                    deploy.Deploy()._apply_state(
                        state, targets=node_id, stages=[state]
                    )
                except Exception as ex:
                    raise ex

    def run(self):
        """Node Prepare command .
        It would deploy platform states and prepare cortx components.

        Execution:
        `cortx_setup node prepare cortx`
        """

        self.logger.debug("Deploying platform components")
        self._deploy(provisioner_components['platform'])

        self.logger.debug("Deploying cortx components")
        self._deploy(cortx_components, stage="prepare")
