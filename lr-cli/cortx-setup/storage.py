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

# Cortx Setup API for Storage Enclosure


import logging

from provisioner.commands import (
     PillarSet
)
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)


class Storage:

    def pillar_set(self, *args, **kwargs):
        """Sets values to and from pillar. """

        resp = True
        try:
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


    def config(targets=local_minion_id()):
        """storage config command execution method.

        Execution:
        `cortx_setup storage config ...`

        """
