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

import os
from provisioner.salt import (
    cmd_run,
    local_minion_id,
    StateFunExecuter,
    StatesApplier
)
from provisioner.config import PRVSNR_ROOT_DIR
from .config import NodePrepareServerConfig


class NodePrepareServer(NodePrepareServerConfig):

    def _ip_not_pingable(self, ip: str):
        res = os.system(f"ping -c 1 {ip}")
        return not res == 0

    def run(self, **kwargs):
        super().run(**kwargs)
        node = local_minion_id()
        mgmt_vip = kwargs.get('mgmt_vip')

        try:
            if self._ip_not_pingable(mgmt_vip):
                self.logger.debug(
                    f"Aliasing {mgmt_vip} to public managemnt Interface on primary node")
                state = "components.system.network.mgmt.ip_alias"
                self.logger.debug(f"Applying {state} on {node}")
                StatesApplier.apply([state])
            else:
                self.logger.warning(
                    f"Unable to alias IP to management network . The IP {mgmt_vip} is already in use")

            self.logger.debug("Updating salt-minion file")
            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name="/etc/salt/minion",
                    source=str(PRVSNR_ROOT_DIR) +
                    'srv/components/provisioner/salt_minion/files/minion_factory',
                    template='jinja'
                )
            )
            self.logger.debug("Restarting salt-minion")
            cmd_run(
                "systemctl restart salt-minion",
                background=True,
                targets=node
            )

        except Exception as e:
            raise e
