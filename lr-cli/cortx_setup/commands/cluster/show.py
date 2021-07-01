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

import json
from ..command import Command
from provisioner.salt import local_minion_id, cmd_run


class ClusterShow(Command):

    def run(self):
        res = cmd_run('salt-key -L --out=json')
        res = json.loads(res[local_minion_id()])
        result = {}
        result['cluster_nodes'] = res.get('minions')
        result['non_cluster_nodes'] = res.get('minions_pre')
        return result
