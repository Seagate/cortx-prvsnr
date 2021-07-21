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

from pathlib import Path
from ..command import Command
from cortx_setup.commands.common_utils import get_pillar_data
from cortx_setup.config import CERT_PATH, HEALTH_PATH  # , MANIFEST_PATH
from cortx_setup.validate import (
    CortxSetupError,
    interfaces,
    disk_devices
)
from provisioner.config import SEAGATE_USER_HOME_DIR
from provisioner.salt import local_minion_id, StateFunExecuter
from provisioner.values import MISSED


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
        resource_paths = [HEALTH_PATH]    # [HEALTH_PATH, MANIFEST_PATH]
        for resource in resource_paths:
            path = get_pillar_data(resource)
            if not path or path is MISSED:
                raise CortxSetupError(f"{resource} resource is not configured")
            path = path.split('://')[1]
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
                "Validation failed: "
                f"Cert file not present {cert_file}"
            )
        self.logger.debug("Certificate installtion check: Success")


    def _validate_interfaces(self, node_id):
        self.logger.debug("Validating network interfaces check")
        mgmt = get_pillar_data(f'cluster/{node_id}/network/mgmt/interfaces')
        private_data = get_pillar_data(f'cluster/{node_id}/network/data/private_interfaces')  # noqa: E501
        public_data = get_pillar_data(f'cluster/{node_id}/network/data/public_interfaces')  # noqa: E501
        if not mgmt or mgmt is MISSED:
            raise CortxSetupError("Mgmt interfaces are not provided")
        if not private_data or private_data is MISSED:
            raise CortxSetupError("Private data interfaces are not provided")
        if not public_data or public_data is MISSED:
            raise CortxSetupError("Public data interfaces are not provided")

        for interface in mgmt:
            if interface in private_data or interface in public_data:
                raise CortxSetupError(
                    "Same interface provided for mgmt and data")

        for interface in private_data:
            if interface in public_data:
                raise CortxSetupError(
                    f"Same interface provided for public_data "
                    f"{public_data}& private_data: {private_data}"
                )
        interfaces(mgmt + private_data + public_data)
        self.logger.debug("Network interfaces check: Success")


    def _validate_devices(self, node_id, s_type):
        self.logger.debug("Validating cvg devices check")
        cvgs = get_pillar_data(f'cluster/{node_id}/storage/cvg')
        if not cvgs or cvgs is MISSED:
            raise CortxSetupError("Devices are not provided")
        for cvg in cvgs:
            meta_data = cvg.get('metadata_devices')
            data = cvg.get('data_devices')
            if not meta_data or not data:
                raise CortxSetupError("metadata or data devices are missing")

            for meta in meta_data:
                if meta in data:
                    raise CortxSetupError(
                        f"{meta} is common in metadata and data device list")
            disk_devices(s_type, data + meta_data)
        self.logger.debug("Cvg devices check: Success")


    def _validate_server_type(self, node_id):
        self.logger.debug("Validating server type check")
        server_type = get_pillar_data(f'cluster/{node_id}/type')
        if not server_type or server_type is MISSED:
            raise CortxSetupError("Server type is not provided")
        self.logger.debug("Server type check: Success")
        return server_type



    def _create_field_users(self, node_id):
        """users creation.

        Creates field users - `nodeadmin` and `support`
        with specific permissions each

        """
        # More Field users can be added to this list in future
        for user in ['nodeadmin', 'support']:
            home_dir = SEAGATE_USER_HOME_DIR / user
            Path(home_dir).mkdir(parents=True, exist_ok=True)

            if "nodeadmin" in user:
                ugroup = "prvsnrusers"
                user_permissions = [
                    '/usr/bin/nodecli',
                    '/var/log'
                ]
                default_login = "/usr/bin/bash"
            else:
                ugroup = "wheel"
                user_permissions = ['ALL']
                default_login = "/usr/bin/bash"

            self.logger.debug(
               f"Creating user group '{ugroup}', if not present"
            )
            StateFunExecuter.execute(
                'group.present',
                fun_kwargs=dict(
                    name=ugroup
                ),
                targets=node_id
            )

            self.logger.debug(f"Creating user: '{user}'")
            StateFunExecuter.execute(
                'user.present',
                fun_kwargs=dict(
                    name=user,
                    password="Seagate123!",     # TODO: remove from cli, add this to vault in future
                    hash_password=True,
                    home=str(home_dir),
                    groups=[ugroup],
                    shell=default_login        # nosec
                ),
                targets=node_id,
                secure=True
            )

            self.logger.debug(f"Creating sudoers file with permissions for user: '{user}'")

            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=f"/etc/sudoers.d/{user}",
                    contents=(f'## Restricted access for {user} group users \n'
                              f'%{user}   ALL = NOPASSWD: '
                              f'{", ".join(user_permissions)}'),
                    create=True,
                    replace=True,
                    user='root',
                    group='root',
                    mode=440
                ),
                targets=node_id
            )

            self.logger.debug(f"Success: User creation for '{user}'")

            if "nodeadmin" in user:
                self.logger.debug(
                  f"Adding assistance to change default password on first login for '{user}' user"
                )
                StateFunExecuter.execute(
                    'cmd.run',
                    fun_kwargs=dict(
                        name=f'passwd -e {user}'
                    ),
                    targets=node_id
                )

                self.logger.debug("Ensuring user permissions on system")

                StateFunExecuter.execute(
                    'file.append',
                    fun_kwargs=dict(
                        name=f'{home_dir}/.profile',
                        text=('sudo /usr/bin/nodecli \n'
                              'alias exit=exit;exit')
                    ),
                    targets=node_id
                )


    def run(self, force=False):
        try:
            node_id = local_minion_id()
            self._validate_cert_installation()
            self._validate_health_map()
            self._validate_interfaces(node_id)
            server_type = self._validate_server_type(node_id)
            self._validate_devices(node_id, server_type)

            self.logger.info(
                "Node validations complete. Creating Field users.."
            )
            self._create_field_users(node_id)
            self.logger.debug("Field users created.")

        except CortxSetupError as exc:
            if force:
                self.logger.info(
                    f"One or more node validation(s) failed: {str(exc)}.\n"
                    "Forcibly creating users.."
                )
                self._create_field_users(node_id)
                self.logger.info(
                  "Field users created. Check logs for more details on the validations error..")
            else:
                raise
