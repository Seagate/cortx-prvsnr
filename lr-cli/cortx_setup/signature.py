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


import logging

from provisioner.commands import (
     PillarGet,
     PillarSet
)
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)


class Signature:

    def get(key=None):
        """signature get command execution method.

        (Specific only to current(given) node.)
        Gets LR Signature.

        Execution:
        `cortx_setup signature get --key 'key'`

        """
        try:
            targets = local_minion_id()
            node_data = PillarGet().run(
                          "node", targets=targets
                          )[targets]

            # Reference: cortx_setup/sample.json

            if 'signature' not in node_data['node'][targets]:
                user_msg = ("Node Signature was never set in database. "
                            "Execute `signature set` command to set it.")
                logger.error(user_msg)
                raise Exception(user_msg)

            if key:
                lr_sign = node_data['node'][targets]['signature'][key]
            else:
                lr_sign = node_data['node'][targets]['signature']

            return f"LR Signature: {lr_sign}"

        except ValueError as exc:
            raise ValueError(
                "Failed: Encountered error while retrieving "
                f"LR signature from database: {str(exc)}"
            )

    def set(key=None, value=None, signature=None):
        """signature set command execution method.

        (Specific only to current(given) node.)
        Sets LR signature.

        Execution:
        `cortx_setup signature set --key 'key' --value 'value'`
        OR
        `cortx_setup signature set --signature {'key': 'value'}`

        """
        try:
            targets = local_minion_id()
            key_path = f"node/{targets}/signature"
            lr_sign = {}

            node_data = PillarGet().run("node", targets=targets)[targets]

            if 'signature' in node_data['node'][targets]:
                lr_sign = node_data['node'][targets]['signature']

            if key and value:
                lr_sign.update({key: value})

            elif signature:
                if not isinstance(signature, dict):
                    user_msg = ("Expected dictionary format for "
                                "node signature: {'key': 'value'}")
                    logger.error(user_msg)
                    raise Exception(user_msg)

                lr_sign.update(signature)

            else:
                user_msg = ("A valid signature format is mandatory to set for stamping. "
                            "Expected Signature formats: \"{'key': 'value'} \" "
                            "or \"--key 'key' --value 'value' \"."
                            )
                logger.error(user_msg)
                raise Exception(user_msg)

            PillarSet().run(
                   key_path,
                   lr_sign,
                   targets=targets
                )

            return "Success: Stamping done for current node and database updated."

        except Exception as exc:
            raise ValueError(
                "Failed: Encountered error while setting "
                f"LR signature to database: {str(exc)}"
            )
