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
# Cortx Setup API to refresh enclosure_id


from ..command import Command
from cortx_setup.config import (
    ALL_MINIONS
)
from provisioner.salt import StatesApplier


class RefreshEnclosureId(Command):
    """
    Refresh EnclosureId
    """

    _args = {}
    def run(self, targets=ALL_MINIONS, **kwargs):
        try:
            self.logger.debug("Refresh enclosure ID")

            for state in [
                'components.system.storage.enclosure_id',
                'components.system.config.sync_salt'
            ]:
                StatesApplier.apply([state], targets, **kwargs)

        except Exception as exc:
            self.logger.error(
               f"Error in refreshing enclosure ID. Reason: '{str(exc)}'"
            )
