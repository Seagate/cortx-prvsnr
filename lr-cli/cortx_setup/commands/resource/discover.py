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

import time
from ..command import Command
from provisioner.commands import PillarSet
from cortx.utils.discovery import Discovery
from cortx_setup.config import RETRIES, WAIT


class ResourceDiscover(Command):

    def get_resource_map(self, resource_type=None):

        retries = RETRIES
        status = ""
        self.logger.debug("Running resource discover command")
        # Currently since this is a bug once fixed (EOS-20937)
        # we wont be needing to provide any parameter
        request_id = Discovery.generate_node_health(rpath=resource_type)
        self.logger.debug(f"Requestid for resource map - {request_id}")

        while retries > 0:
            status = Discovery.get_gen_node_health_status(request_id)
            if "Success" in status:
                break
            elif "Failed" in status:
                raise Exception(status)
            retries -= 1
            time.sleep(WAIT)
        else:
            if retries == 0 and "Success" not in status:
                raise Exception(
                    "Timed out error."
                    "Generation of resource map is taking longer than expected.")

        return Discovery.get_node_health(request_id)

    _args = {}

    def run(self):

        resource_path = self.get_resource_map()
        PillarSet().run(
            'provisioner/common_config/resource_map_path',
            resource_path,
            local=True
        )
        self.logger.debug(f"Resource map present at - {resource_path}")
        self.logger.debug(f"Done")
