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
# Cortx Setup API to encrypt pillar values


from ..command import Command
from cortx_setup.config import (
    ALL_MINIONS
)
import provisioner
from provisioner.salt import StatesApplier


class EncryptSecrets(Command):
    """
    Encrypt config data
    """

    _args = {}
    def run(self, targets=ALL_MINIONS, **kwargs):

        self.provisioner = provisioner
        self.provisioner.auth_init(kwargs['username'], kwargs['passowrd'])

        try:
            self.logger.debug("Encrypting config data")

            for state in [
                'components.system.config.pillar_encrypt',
                'components.system.config.sync_salt'
            ]:
                StatesApplier.apply([state], targets, **kwargs)

        except Exception as exc:
            self.logger.error(
               f"Error in data encryption. Reason: '{str(exc)}'"
            )
