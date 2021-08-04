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
from cortx_setup.commands.common_utils import (
    get_reset_states
)
from provisioner.config import ALL_MINIONS
from provisioner.commands import (
    deploy
)
from provisioner.salt import (
    StatesApplier,
    cmd_run,
    local_minion_id
)
class ClusterResetNode(Command):
    _args = {
        'type': {
            'type': str,
            'optional': True,
            'help': 'reset all/data'
        }
    }

    # deploy the specific component states wrt to stages like reset,cleanup
    def _destroy(self, components: dict, stage: list = None):
        for component in components:
            states = components[component]
            for state in states:
                try:
                    self.logger.debug(
                        f"Running {state} for ALL_MINIONS"
                    )
                    deploy.Deploy()._apply_state(
                        f'components.{state}', targets= ALL_MINIONS, stages=stage
                    )
                except Exception as ex:
                    raise ex

    @staticmethod
    def cluster_stop():
        res = cmd_run('cortx cluster stop --all', targets=local_minion_id())
        return next(iter(res.values()))

    @staticmethod
    def cluster_start():
        res = cmd_run('cortx cluster start', targets=local_minion_id())
        return next(iter(res.values()))

    def run(self, **kwargs):

        if kwargs['type'] == 'data':
            self.logger.info("Stopping the cluster")
            self.cluster_stop()

            self.logger.info("Calling reset for cortx components")
            cortx_components = get_reset_states()
            self._destroy(cortx_components, stage=["teardown.reset"])

            self.logger.info("Cleaning up provisioner logs and metadata")
            StatesApplier.apply(
                ["components.provisioner.teardown.reset"],
                targets=ALL_MINIONS
            )

            self.logger.info("starting the cluster")
            self.cluster_start()
            self.logger.info("Done")
