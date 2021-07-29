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
from cortx_setup.config import (
    WAIT,
    RETRIES,
    HEALTH_PATH,
    MANIFEST_PATH
)
from cortx_setup.validate import CortxSetupError


class ResourceDiscover(Command):

    def get_resource_map(self, resource_type=None):

        retries = RETRIES
        status = ""
        self.logger.debug("Running resource health command")

        request_id = Discovery.generate_node_health(rpath=resource_type)
        self.logger.debug(f"Requestid for resource map - {request_id}")

        while retries > 0:
            status = Discovery.get_gen_node_health_status(request_id)
            if "Success" in status:
                break
            elif "Failed" in status:
                raise CortxSetupError(status)
            retries -= 1
            time.sleep(WAIT)
        else:
            if retries == 0 and "Success" not in status:
                raise CortxSetupError(
                    "Timed out error."
                    "Generation of resource map is taking longer than expected.")

        return Discovery.get_node_health(request_id)

    def get_node_manifest(self, resource_type=None):

        retries = RETRIES
        status = ""
        self.logger.debug("Running resource manifest command")

        request_id = Discovery.generate_node_manifest(rpath=resource_type)
        self.logger.debug(f"Requestid for manifest - {request_id}")

        while retries > 0:
            status = Discovery.get_gen_node_manifest_status(request_id)
            if "Success" in status:
                break
            elif "Failed" in status:
                raise CortxSetupError(status)
            retries -= 1
            time.sleep(WAIT)
        else:
            if retries == 0 and "Success" not in status:
                raise CortxSetupError(
                    "Timed out error."
                    "Generation of node manifest is taking longer than expected.")

        return Discovery.get_node_manifest(request_id)

    _args = {}

    def run(self):

        resource_path = self.get_resource_map()
        PillarSet().run(
            HEALTH_PATH,
            resource_path,
            local=True
        )
        self.logger.debug(f"Resource map present at - {resource_path}")

        manifest_path = self.get_node_manifest()
        PillarSet().run(
            MANIFEST_PATH,
            manifest_path,
            local=True
        )
        self.logger.debug(f"Node manifest present at - {manifest_path}")
        self.logger.debug(f"Done")
