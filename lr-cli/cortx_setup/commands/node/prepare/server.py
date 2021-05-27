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

from provisioner.salt import (
    cmd_run,
    local_minion_id,
    StateFunExecuter,
    StatesApplier
)
from .config import NodePrepareServerConfig
from .common_utils import get_pillar_data


class NodePrepareServer(NodePrepareServerConfig):

    def _ip_not_pingable(self, ip: str):
        res = cmd_run(f"ping -c 1 {ip}")
        return not res == 0

    def run(self, **kwargs):
        node = local_minion_id()
        mgmt_vip = kwargs.get('mgmt_vip')

        try:
            if "primary" in get_pillar_data(f"cluster/{node}/roles"):
                if self._ip_not_pingable(mgmt_vip):
                    self.logger.info(
                        f"Aliasing {mgmt_vip} to public managemnt Interface on primary node")
                    state = "components.system.network.mgmt.public.ip_alias"
                    self.logger.debug(f"Applying {state} on {node}")
                    StatesApplier.apply([state], node)
                else:
                    raise Exception(f"The IP {mgmt_vip} is in use")

            self.logger.info("Updating salt-minion file")
            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name="/etc/salt/minion",
                    source='salt://' +
                    'srv/components/provisioner/salt_minion/files/minion_factory',
                    template='jinja'
                )
            )
            self.logger.info("Restarting salt-minion")
            cmd_run(
                "salt-call --local service.restart salt-minion",
                targets=node)

        except Exception as e:
            raise e
