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


import subprocess  # noqa
from pathlib import Path
from time import sleep

from ..command import Command

# CORTX package
from cortx.utils.conf_store import Conf


class SetSignature(Command):
    _args = {
        'key': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Signature key to set. e.g: {name|address}'
        },
        'value': {
            'type': str,
            'default': None,
            'optional': True,
            'help': 'Signature value to set. e.g: {node001}'
        }
    }

    def run(self, key=None, value=None):
        """signature set command execution method.

        (Specific only to current(given) node.)
        Sets LR signature.

        Execution:
        `cortx_setup signature set --key key --value value`

        """
        try:
            # Move this definition to common config file
            lr_sign_file = Path("/etc/node-signature.yaml")
            index = "signature"

            if not (key and value):
                raise Exception(
                   "A valid signature is mandatory to set for stamping. "
                   "Expected Signature params format: --key 'key' --value 'value'."
                )

            if not (lr_sign_file.exists() and
                    lr_sign_file.stat().st_size != 0):
                self.logger.warning("Node Signature was never set "
                                    "in ConfStore. Setting now.")

            else:
                # Immutable file. Make it editable first.
                _cmd = f"chattr -i {lr_sign_file}"
                subprocess.Popen(_cmd, shell=True)     # nosec
                # This step takes a second to process.
                sleep(1)

            Conf.load(index, f'yaml://{lr_sign_file}')

            Conf.set(index, f'signature>{key}', f'{value}')
            Conf.save(index)

            # TODO: check if this signature data
            # should be written to grains and in what format.

            # Make the file immutable to any editing
            _cmd = f"chattr +i {lr_sign_file} && lsattr {lr_sign_file}"
            subprocess.Popen(_cmd, shell=True)     # nosec

            return f"Node Stamping done and '{key}' is set as '{value}' in Signature"

        except Exception as exc:
            raise ValueError(
              "Failed to set node signature: %s" % str(exc)
            )
