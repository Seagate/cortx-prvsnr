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
from provisioner.commands.grains_get import GrainsGet
from .command import Command


class SaltCleanup(Command):
    _args = {}

    def _get_grains_id(self):
        res = GrainsGet().run('id')
        if res.get(local_minion_id()):
            result = res.get(local_minion_id())
            if result.get('id'):
                return result.get('id')
        else:
            self.logger.error("No grains id available")

    def run(self):
        minion_id = self._get_grains_id()
        if minion_id:
            self.logger.debug(f"removing minion {minion_id} from salt cluster")
            run_subprocess_cmd(f"salt-key -d {minion_id} -y")
        self.logger.debug("Remove minion_id and minion_master.pub from system")
        run_subprocess_cmd(f"rm -rf /etc/salt/minion_id")
        run_subprocess_cmd(f"rm -rf /etc/salt/pki/minion/minion_master.pub")
        self.logger.debug(f"Minion {minion_id} removed from salt configurtion")
