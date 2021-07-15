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

from cortx_setup.config import CERT_PATH, HEALTH_PATH # , MANIFEST_PATH
from provisioner.salt import local_minion_id, StateFunExecuter
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
        check = True
        self.logger.debug("Validating node health check")
        resource_paths = [HEALTH_PATH]    #[HEALTH_PATH, MANIFEST_PATH]
        for resource in resource_paths:
            path = get_pillar_data(resource)
            if not path or path is MISSED:
                check = False
                self.logger.error(f"{resource} resource is not configured")
            path = path.split('://')[1]
            if not Path(path).is_file():
                check = False
                self.logger.error(f"Validation failed: File not present {path}")
        self.logger.debug("Node health check: Success")
        return check


    def _validate_cert_installation(self):
        check = True
        self.logger.debug("Validating certificate installtion check")
        cert_file = None
        cert_file = Path(CERT_PATH / 'stx.pem')
        if not cert_file.is_file():
            check = False
            self.logger.error(
                "Validation failed: "
                f"Cert file not present {cert_file}"
            )
        self.logger.debug("Certificate installtion check: Success")
        return check


    def _validate_interfaces(self, node_id):
        check = True
        self.logger.debug("Validating network interfaces check")
        mgmt = get_pillar_data(f'cluster/{node_id}/network/mgmt/interfaces')
        private_data = get_pillar_data(f'cluster/{node_id}/network/data/private_interfaces')  # noqa: E501
        public_data = get_pillar_data(f'cluster/{node_id}/network/data/public_interfaces')  # noqa: E501

        if not mgmt or mgmt is MISSED:
            check = False
            self.logger.error("Mgmt interfaces are not provided")

        if not private_data or private_data is MISSED:
            check = False
            self.logger.error("Private data interfaces are not provided")

        if not public_data or public_data is MISSED:
            check = False
            self.logger.error("Public data interfaces are not provided")

        for interface in mgmt:
            if interface in private_data or interface in public_data:
                check = False
                self.logger.error(
                    "Same interface provided for mgmt and data")

        for interface in private_data:
            if interface in public_data:
                check = False
                self.logger.error(
                    "Same interface provided for public_data "
                    f"{public_data}& private_data: {private_data}"
                )
        interfaces(mgmt + private_data + public_data)
        self.logger.debug("Network interfaces check: Success")
        return check


    def _validate_devices(self, node_id, s_type):
        check = True
        self.logger.debug("Validating cvg devices check")
        cvgs = get_pillar_data(f'cluster/{node_id}/storage/cvg')
        if not cvgs or cvgs is MISSED:
            check = False
            self.logger.error("Devices are not provided")
        for cvg in cvgs:
            meta_data = cvg.get('metadata_devices')
            data = cvg.get('data_devices')
            if not meta_data or not data:
                check = False
                self.logger.error("metadata or data devices are missing")

            for meta in meta_data:
                if meta in data:
                    check = False
                    self.logger.error(
                        f"{meta} is common in metadata and data device list")
            disk_devices(s_type, data + meta_data)
        self.logger.debug("Cvg devices check: Success")
        return check


    def _validate_server_type(self, node_id):
        self.logger.debug("Validating server type check")
        server_type = get_pillar_data(f'cluster/{node_id}/type')
        if not server_type or server_type is MISSED:
            self.logger.error("Server type is not provided")
        self.logger.debug("Server type check: Success")
        return server_type


    def _create_field_users(self, node_id):
        """users creation.

        Creates field users - `nodeadmin` and `support`
        with specific permissions each

        """
        user_passwd = "Seagate123!"
#        server_hostname = get_pillar_data(f'cluster/{node_id}/hostname')
        for user in ['nodeadmin', 'support']:
            home_dir = Path(f'/home/{user}')
#            ssh_dir = home_dir / '.ssh'

            ugroup = user if user == "nodeadmin" else "root"

            self.logger.debug(
               f"Creating, if not present, a new user group '{ugroup}'"
            )
            StateFunExecuter.execute(
                'group.present',
                fun_kwargs=dict(
                    name=ugroup
                ),
                targets=node_id
            )

            self.logger.debug(f"Creating sudoers file with permissions for user: '{user}'")
            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=f"/etc/sudoers.d/{user}",
                    contents=(f'## Restricted access for {user} group users \n'
                              f'%{user}   ALL = NOPASSWD: '
                              '/opt/seagate/cortx/provisioner/node_cli/'),
                    create=True,
                    replace=True,
                    user=ugroup,
                    group=ugroup,
                    mode=440
                ),
                targets=node_id
            )

            self.logger.debug(f"Creating user: '{user}'")
            StateFunExecuter.execute(
                'user.present',
                fun_kwargs=dict(
                    name=user,
                    password=user_passwd,
                    hash_password=True,
                    home=str(home_dir),
                    groups=ugroup,
                    shell="/opt/seagate/cortx/provisioner/node_cli/"
                ),
                targets=node_id,
                secure=True
            )

            self.logger.debug(f"Success: User creation for '{user}'")


    def run(self, force=False):
        node_id = local_minion_id()
        val_1 = self._validate_cert_installation()
        val_2 = self._validate_health_map()
        val_3 = self._validate_interfaces(node_id)
        s_type = self._validate_server_type(node_id)
        val_4 = self._validate_devices(node_id, s_type)

        if (val_1 and val_2 and val_3 and val_4):
            self.logger.info(
                "Node validations complete. Proceeding to create users.."
            )
        else:
            if force:
                self.logger.info(
                    "One or more node validation(s) failed. Forcibly creating users.."
                )
            else:
                raise CortxSetupError(
                    "One or more node validation(s) failed. Check logs for more details."
                )

        self._create_field_users(node_id)
        self.logger.debug("Node validations all done and Field users created.")
