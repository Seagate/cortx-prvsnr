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

# Cortx Setup API for Node Stamping Signature operations


import argparse
import logging
import subprocess  # noqa
import yaml

from pathlib import Path

# CORTX package
from cortx.utils.conf_store import Conf

logger = logging.getLogger(__name__)


class Signature:

    @staticmethod
    def get(**kwargs):
        """signature get command execution method.

        (Specific only to current(given) node.)
        Gets LR Signature.

        Execution:
        `cortx_setup signature get --key 'key'`

        """
        try:
            index = 'signature'
            lr_sign_file = Path("/etc/node-signature.yaml")

            if not (lr_sign_file.exists() and
                    lr_sign_file.stat().st_size != 0):

                logger.warning("Node Signature was never set in database. "
                               "Set it first with `signature set` command.")
                lr_sign = "No data found. Execute `signature set` command."

            else:
                Conf.load(index, f'yaml://{lr_sign_file}')
                lr_sign = Conf.get(index, f'signature>{kwargs["key"]}')

                if lr_sign is None:
                    logger.warning(
                       f"Given key '{kwargs['key']}' is possibly "
                       "not found in Signature data."
                    )
                    lr_sign = Conf.get(index, 'signature')

            return f"LR Signature: {lr_sign}"

        except ValueError as exc:
            raise ValueError(
              f"Failed: GET LR signature from ConfStore: {str(exc)}"
            )

    @staticmethod
    def set(**kwargs):
        """signature set command execution method.

        (Specific only to current(given) node.)
        Sets LR signature.

        Execution:
        `cortx_setup signature set --key 'key' --value 'value'`

        """
        try:
            index = 'signature'
            lr_sign_file = Path("/etc/node-signature.yaml")

            if key and value:
                if not (lr_sign_file.exists() and
                        lr_sign_file.stat().st_size != 0):

                    logger.warning("Node Signature was never set "
                                   "in ConfStore. Setting now.")
                    data = {'signature': {}}

                else:
                    # Immutable file. Make it editable first.
                    _cmd = f"chattr -i {lr_sign_file}"
                    subprocess.Popen(_cmd, shell=True)     # nosec

                    with open(lr_sign_file, 'r') as fo:
                        data = yaml.safe_load(fo)

                Conf.load(index, f'yaml://{lr_sign_file}')
                data['signature'].update({key: value})

                with open(lr_sign_file, 'w') as fi:
                    yaml.dump(data, fi, default_flow_style=False)

                Conf.set(index, f'signature>{kwargs["key"]}', f'{kwargs["value"]}')
                Conf.save(index)

                # TODO: With refined approach, check if this signature data
                # should be written to grains. If yes, what format?

                # Make the file immutable for further editing
                _cmd = f"chattr +i {lr_sign_file} && lsattr {lr_sign_file}"
                subprocess.Popen(_cmd, shell=True)     # nosec

            else:
                user_msg = ("A valid signature is mandatory to set for stamping. "
                            "Expected Signature format: \"--key 'key' --value 'value' \"."
                            )
                logger.error(user_msg)
                raise Exception(user_msg)

            return "Success: Stamping done for current node and ConfStore updated."

        except Exception as exc:
            raise ValueError(
              f"Failed: SET LR signature to ConfStore: {str(exc)}"
            )


if __name__ == "__main__":

    # This entire section will be converted (with better design)
    # to a common utility to suit all Factory functionalities:
    # signature, network, storage, node_init, etc.

    parser = argparse.ArgumentParser(
                   description='For Node Signature')
    parser.add_argument('--get',
                        nargs='*',
                        type=str,
                        help='Gets the given signature value from database')
    parser.add_argument('--set',
                        nargs='*',
                        type=str,
                        help='Sets the given signature key:value to database')

    args = vars(parser.parse_args())

    parsed_conf = {}
    for pair in (args['set'] or args['get']):
        key, value = pair.split('=')
        parsed_conf[key] = value

    if args['get']:
        resp = Signature.get(
           key=parsed_conf['key']
        )
    elif args['set']:
        resp = Signature.set(
            key=parsed_conf['key'],
            value=parsed_conf['value']
        )
    print(resp)
