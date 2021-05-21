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
    local_minion_id, 
    StatesApplier
)
from .config import NodePrepareServerConfig

class NodePrepareServer(NodePrepareServerConfig):

    def _ip_not_pingable(ip: str):
        res = os.system("ping -c 1 {ip}")
        return not (res == 0)

    def run(self, **kwargs):
        mgmt_vip = kwargs.get('mgmt_vip')

        try:
            if _ip_not_pingable(mgmt_vip):
                states = [
                    "components.system.network.mgmt.public.ip_alias"
                ]
                for state in states:
                    self.logger.info(f"Applying {state} on {node_id}")
                    StatesApplier.apply([state], local_minion_id())
            else:
                raise Exception("The IP {mgmt_vip} is in use")
        except Exception as e:
            raise e

                