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

from cortx_setup.config import CERT_PATH, HEALTH_PATH, MANIFEST_PATH
from provisioner.salt import local_minion_id
from provisioner.values import MISSED
from cortx_setup.validate import CortxSetupError, interfaces, disk_devices
from ..command import Command
from cortx_setup.commands.common_utils import get_pillar_data
from pathlib import Path


class NodeFinalize(Command):
    _args = {
        'force': {
            'default': False,
            'optional': True,
            'action': 'store_true',
            'help': 'Forcefully apply configuration.'
        }
    }

    def _validate_health_map(self):
        self.logger.debug("Validating node health check")
        resource_paths = [HEALTH_PATH, MANIFEST_PATH]
        for resource in resource_paths:
            path = get_pillar_data(resource)
            if not path or path is MISSED:
                raise CortxSetupError(f"{resource} resource is not configured")
            if not Path(path).is_file():
                raise CortxSetupError(f"Validation failed: "
                                      f"File not present {path}")
        self.logger.debug("Node health check: Success")

    def _validate_cert_installation(self):
        self.logger.debug("Validating certificate installtion check")
        cert_file = None
        cert_file = Path(CERT_PATH / 'stx.pem')
        if not cert_file.is_file():
            raise CortxSetupError(
                f"Validation failed: "
                f"Cert file not present {cert_file}"
            )
        self.logger.debug("Certificate installtion check: Success")

    def _validate_interfaces(self, minion_id):
        self.logger.debug("Validating network interfaces check")
        mgmt = get_pillar_data(f'cluster/{minion_id}/network/mgmt/interfaces')
        private_data = get_pillar_data(f'cluster/{minion_id}/network/data/private_interfaces')  # noqa: E501
        public_data = get_pillar_data(f'cluster/{minion_id}/network/data/public_interfaces')  # noqa: E501
        if not mgmt or mgmt is MISSED:
            raise CortxSetupError(f"Mgmt interfaces are not provided")
        if not private_data or private_data is MISSED:
            raise CortxSetupError(f"Private data interfaces are not provided")
        if not public_data or public_data is MISSED:
            raise CortxSetupError(f"Public data interfaces are not provided")

        for interface in mgmt:
            if interface in private_data or interface in public_data:
                raise CortxSetupError(
                    f"Same interface provided for mgmt and data")

        for interface in private_data:
            if interface in public_data:
                raise CortxSetupError(
                    f"Same interface provided for public_data "
                    f"{public_data}& private_data: {private_data}"
                )
        interfaces(mgmt + private_data + public_data)
        self.logger.debug("Network interfaces check: Success")

    def _validate_devices(self, minion_id, s_type):
        self.logger.debug("Validating cvg devices check")
        cvgs = get_pillar_data(f'cluster/{minion_id}/storage/cvg')
        if not cvgs or cvgs is MISSED:
            raise CortxSetupError(f"Devices are not provided")
        for cvg in cvgs:
            meta_data = cvg.get('metadata_devices')
            data = cvg.get('data_devices')
            if not meta_data or not data:
                raise CortxSetupError(f"metadata or data devices are missing")

            for meta in meta_data:
                if meta in data:
                    raise CortxSetupError(
                        f"{meta} is common in metadata and data device list")
            disk_devices(s_type, data + meta_data)
        self.logger.debug("Cvg devices check: Success")

    def _validate_server_type(self, minion_id):
        self.logger.debug("Validating server type check")
        server_type = get_pillar_data(f'cluster/{minion_id}/type')
        if not server_type or server_type is MISSED:
            raise CortxSetupError(f"Server type is not provided")
        self.logger.debug("Server type check: Success")
        return server_type

    def run(self, force=False):
        local_minion = local_minion_id()
        self._validate_cert_installation()
        self._validate_health_map()
        self._validate_interfaces(local_minion)
        s_type = self._validate_server_type(local_minion)
        self._validate_devices(local_minion, s_type)
        self.logger.debug("Done")
