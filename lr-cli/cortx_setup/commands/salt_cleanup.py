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

from provisioner.salt import local_minion_id
from provisioner.utils import run_subprocess_cmd
from .command import Command


class SaltCleanup(Command):

    def run(self):
        minion_id = local_minion_id()
        if minion_id:
            self.logger.debug(f"removing minion {minion_id} from salt cluster")
            run_subprocess_cmd(f"salt-key -d {minion_id} -y")
        self.logger.debug("Remove minion_id and minion_master.pub from system")
        run_subprocess_cmd(f"rm -rf /etc/salt/minion_id")
        run_subprocess_cmd(f"rm -rf /etc/salt/pki/minion/minion_master.pub")
        self.logger.debug(f"Minion {minion_id} removed from salt configurtion")
