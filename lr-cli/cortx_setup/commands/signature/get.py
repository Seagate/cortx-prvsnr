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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

# Cortx Setup API for LR-Node Stamping Signature operations


from pathlib import Path
from ..command import Command

# CORTX package
from cortx.utils.conf_store import Conf


class GetSignature(Command):
    _args = {
        'key': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Signature details to retrieve for this key'
        }
    }

    def run(self, key=None):
        """signature get command execution method.

        (Specific only to current(given) node.)
        Gets LR Signature.

        Execution:
        `cortx_setup signature get --key key`

        """
        try:
            lr_sign_file = Path("/etc/node-signature.yaml")
            index = "signature"

            if not key:
                raise Exception(
                   "Invalid input. Expected Signature param format: --key 'key'."
                )

            if not (lr_sign_file.exists() and
                    lr_sign_file.stat().st_size != 0):

                raise Exception(
                   "Node Signature was never set in ConfStore. "
                   "Set it first with `signature set` command."
                )

            Conf.load(index, f'yaml://{lr_sign_file}')
            lr_sign = Conf.get(index, f'signature>{key}')
            self.logger.info("Signature value for '%s': %s" % (key,lr_sign))

            if not lr_sign:
                lr_sign = Conf.get(index, 'signature')
                self.logger.warning(
                   "Given key '%s' is possibly not found "
                   "in the following Signature data:\n%s" % (key,lr_sign)
                )

        except ValueError as exc:
            raise ValueError(
              "Failed to get node signature from ConfStore: %s" % str(exc)
            )
