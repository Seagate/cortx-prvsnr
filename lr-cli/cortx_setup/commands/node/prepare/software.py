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

from api.python.provisioner import node
from provisioner.config import ALL_MINIONS
from cortx_setup.commands.command import Command
from provisioner.commands import (
    deploy
)
from cortx_setup.commands.common_utils import (
    get_provisioner_states,
    get_cortx_states,
    get_pillar_data
)


class NodePrepare(Command):
    """Cortx Setup API for preparing node"""
    _args = {}

    # deploy the specific component states wrt to stages like prepare, config,
    # post_install
    def _deploy(self, components: dict, stage: list = None):
        for component in components:
            states = components[component]
            for state in states:
                try:
                    self.logger.debug(
                        f"Running {state} for ALL_MINIONS"
                    )
                    deploy.Deploy()._apply_state(
                        f'components.{state}', targets=ALL_MINIONS, stages=stage
                    )
                except Exception as ex:
                    raise ex

    def run(self, **kwargs):
        """Node Prepare command .
        It would deploy platform states and prepare cortx components.

        Execution:
        `cortx_setup node prepare software`
        """

        # provisioner_components = get_provisioner_states()
        cortx_components = get_cortx_states()

        # self.logger.debug("Deploying platform components")
        # self._deploy(
        #     {'noncortx_component': provisioner_components['platform']}, stage=None)

        self.logger.debug("Deploying cortx components")
        self._deploy(cortx_components, stage=["config.prepare"])
