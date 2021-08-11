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


class ClusterStatus(Command):

    def run(self):
        res = cmd_run('hctl status --json', targets=local_minion_id())
        res = json.loads(res[local_minion_id()])
        result = {}
        result['pools'] = res.get('pools')
        result['profiles']= res.get('profiles')
        result['filesystem']=res.get('filesystem')
        result['nodes']= res.get('nodes')
        return res
