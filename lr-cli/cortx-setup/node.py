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

# Cortx Setup API for Node Stamping

# Node stamping is the process where necessary signature and information
# about LR solution is embedded in the node so that this info
# can be used while joining with other similar nodes at the field.


import logging

from provisioner.commands import (
     PillarGet,
     PillarSet
)
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)


class Signature:

#    def pillar_op(self, op, targets, key_path=None, value=None):

    def pillar_op(self, *args, **kwargs):
        """Sets and Gets values to and from pillar. """

        resp = True
        try:
            if kwargs['op'] == 'get':
                pillar_load = PillarGet().run(
                           *args,
                           targets=local_minion_id()
                           )[local_minion_id()]

                # Please check cortx-setup/sample.py
                resp = pillar_load['node'][local_minion_id()]['signature']

            elif kwargs['op'] == 'set':
                PillarSet().run(
                       kwargs[key_path],
                       kwargs[value],
                       targets=local_minion_id()
                       )

        except Exception as exc:
            resp = False
            logger.error(
                f"Error in Pillar operations: {str(exc)}"
            )

        return resp


    def get(targets=local_minion_id()):
        """signature get command execution method.

        (Specific only to current(given) node.)
        Gets LR Signature.

        Execution:
        `cortx_setup signature get`

        """
        try:
            lr_sign = self.pillar_op('get', targets)

            return lr_sign

        except ValueError as exc:
            raise ValueError(
                "Failed: Encountered error while retrieving "
                f"LR signature from ConfStore: {str(exc)}"
            )


    def set(targets=local_minion_id(), lr_sign):
        """signature set command execution method.

        (Specific only to current(given) node.)
        Sets LR signature.

        Execution:
        `cortx_setup signature set <lr_sign>`

        """
        try:

            path_to_set = f"node/{targets}/signature"

            # if value is not provided, set a default one like this
            #value_to_set = targets + 'ABC'

            value_to_set = lr_sign
            self.pillar_op('set', targets, path_to_set, value_to_set)
            return "Success: LR Stamping done for current node and ConfStore updated"

        except Exception as exc:
            raise ValueError(
                "Failed: Encountered error while setting "
                f"LR signature to ConfStore: {str(exc)}"
            )
