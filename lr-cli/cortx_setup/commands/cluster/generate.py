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
# Cortx Setup API to generate cluster


from ..command import Command
from cortx_setup.config import (
    ALL_MINIONS
)
import provisioner
from provisioner.salt import (
    pillar_refresh,
    StatesApplier
)

class GenerateCluster(Command):
    """
    Generate Cluster with sync'ed data
    """

    def run(self, **kwargs):

        self.provisioner = provisioner
        if 'username' in kwargs:
            self.provisioner.auth_init(kwargs['username'], kwargs['password'])

        try:
            self.logger.debug("Generating cluster pillar")

            StatesApplier.apply(
                       ['components.provisioner.config.generate_cluster_pillar',
                        'components.system.config.sync_salt'
                       ],
                       targets=ALL_MINIONS,
                       **kwargs
            )

            self.logger.debug("Refreshing config")
            pillar_refresh(targets=ALL_MINIONS, **kwargs)

        except Exception as exc:
            self.logger.error(
               f"Error in cluster generation. Reason: '{str(exc)}'"
            )
