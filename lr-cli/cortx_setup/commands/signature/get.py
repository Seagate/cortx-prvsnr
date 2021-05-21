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
            'optional': False,
            'help': 'Retrieves the given signature key from ConfStore'
        }
    }

    def run(self, key=None):
        """signature get command execution method.

        (Specific only to current(given) node.)
        Gets LR Signature.

        Execution:
        `cortx_setup signature get --key 'key'`

        """
        try:
            lr_sign_file = Path("/etc/node-signature.yaml")
            index = "signature"

            if not (lr_sign_file.exists() and
                    lr_sign_file.stat().st_size != 0):

                self.logger.warning("Node Signature was never set in database. "
                               "Set it first with `signature set` command.")
                lr_sign = "No data found. Execute `signature set` command."

            else:
                Conf.load(index, f'yaml://{lr_sign_file}')
                lr_sign = Conf.get(index, f'signature>{key}')

                if not lr_sign:
                    self.logger.warning(
                       "Given key '%s' is possibly "
                       "not found in Signature data." % key
                    )
                    lr_sign = Conf.get(index, 'signature')

            self.logger.info(f"LR Signature: {lr_sign}")
            return f"LR Signature: {lr_sign}"

        except ValueError as exc:
            raise ValueError(
              "Failed: GET LR signature from ConfStore: %s" % str(exc)
            )
