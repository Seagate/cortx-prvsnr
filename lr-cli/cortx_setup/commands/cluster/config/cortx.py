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

cortx_components = dict(
    utils=[
        "cortx_utils"
    ],
    iopath=[
        "motr",
        "s3server",
        "hare"
    ],
    controlpath=[
        "sspl",
        "uds",
        "csm"
    ],
    ha=[
        "ha.cortx-ha"
    ]
)


from cortx_setup.commands.command import Command
from provisioner.commands import deploy
from provisioner.salt import local_minion_id

"""Cortx Setup API for configuring cortx"""


class CortxClusterConfig(Command):
    _args = {}

    def configure_cortx(self):

        """Invoke config command for all cortx components"""

        node_id = local_minion_id()

        for component in cortx_components:
            states = cortx_components[component]
            for state in states:
                try:
                    self.logger.debug(
                        f"Invoking config command for {state} component"
                    )
                    deploy.Deploy()._apply_state(
                        f"components.{state}", targets=node_id,
                        stages='config.config'
                    )
                    self.logger.debug(
                        f"Invoking init command for {state} component"
                    )
                    deploy.Deploy()._apply_state(
                        f"components.{state}", targets=node_id,
                        stages='config.init_mod'
                    )
                except Exception as ex:
                    raise ex

    def run(self):

        self.logger.debug("Configuring cortx components on nodes")
        self.configure_cortx()
