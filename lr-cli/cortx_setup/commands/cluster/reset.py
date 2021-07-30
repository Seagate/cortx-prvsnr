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
    get_cleanup_states
)
from provisioner.config import ALL_MINIONS
from provisioner.commands import (
    deploy
)
from provisioner.salt import cmd_run
from cortx_setup.config import (
    PRVSNR_LOG_DIR
)

class NodeResetCluster(Command):
    _args = {
        'type': {
            'type': str,
            'optional': True,
            'help': 'reset all/data'
        }
    }

    # deploy the specific component states wrt to stages like reset,cleanup
    def _deploy(self, components: dict, stage: list = None):
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

    def cluster_stop(self):
        res = cmd_run('pcs cluster stop --all', targets=ALL_MINIONS)
        return next(iter(res.values()))

    def cluster_start(self):
        res = cmd_run('pcs cluster start --all', targets=ALL_MINIONS)
        return next(iter(res.values()))

    def run(self, **kwargs):
        reset_type= kwargs.get('type')
        self.logger.info(f"reset to be done for type is {reset_type}")

        if kwargs['type'] == 'data':
            self.logger.info("cleaning up data and logs")
            res = self.cluster_stop()
            self.logger.info(f"{res}")

            self.logger.info("Calling reset for cortx components")
            cortx_components = get_cleanup_states()
            self._deploy(cortx_components, stage=["teardown.reset"])

            self.logger.info("Cleaning up provisioner logs and metadata")
            res = cmd_run(f"rm -rf {PRVSNR_LOG_DIR}/*", targets=ALL_MINIONS)

            res= self.cluster_start()
            self.logger.info(f"{res}")
