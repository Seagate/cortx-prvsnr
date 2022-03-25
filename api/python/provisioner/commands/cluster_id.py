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

# Python API to ensure ClusterID is unique and returns it to user

import logging
import uuid
from typing import Type

from . import (
     CommandParserFillerMixin
)
from .. import (
    inputs,
    values
)
from provisioner.api import grains_get

from provisioner.commands import (
     PillarGet,
     PillarSet
)
from provisioner.config import (
     CLUSTER_ID_FILE,
     ALL_MINIONS
)
from provisioner.salt import (
     local_minion_id,
     StatesApplier
)
from provisioner.vendor import attr

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ClusterId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def _initial_check(self, role, pillar_cluster_id):
        """Pre-checks

        checks:
          cluster-id setup file and data.
          If not present, generates a uuid and writes to file.

        returns:
          cluster_id value from file

        """
        try:
            if (self.is_exists() and self.is_loaded()):
                cluster_id = CLUSTER_ID_FILE.read_text().replace('\n', '')

            else:
                # Case: When adding a new node to cluster, id is set
                # in pillar, but cluster-id file is not created.
                if pillar_cluster_id:
                    logger.debug("ClusterID file to be created and value written.")
                    cluster_id = pillar_cluster_id

                else:
                    if role != "primary":
                        raise ValueError(
                           "ClusterID can be set only on the Primary node "
                           f"of the cluster. Role of current node: '{role}'. "
                           "Run the same command from the Primary node."
                        )
                    else:
                        logger.debug("ClusterID file does not exist "
                                    "or is empty. Generating an ID to set..")

                        cluster_id = str(uuid.uuid4())


            return cluster_id

        except Exception as exc:
            raise ValueError(
                f"Failed: cluster_id assignment initial check: {str(exc)}"
            )

    def is_exists(self):
        """returns: True if file exists."""

        return CLUSTER_ID_FILE.exists()

    def is_loaded(self):
        """returns: True if file has value and not empty."""

        res = True
        if CLUSTER_ID_FILE.stat().st_size == 0:
            res = False

        return res


    def _get_cluster_id(self, targets=ALL_MINIONS):
        """Gets cluster_id value from pillar and returns to user."""

        res = None
        try:
            cluster_data = PillarGet().run('cluster', targets)
            cluster_id= []
            if cluster_data[local_minion_id()]["cluster"] is values.MISSED:
                logger.debug(
                    "Cluster data is not yet formed and ClusterID not found"
                )
            else:
                for node in cluster_data:
                    if ("cluster_id" not in cluster_data[node]["cluster"] or
                        cluster_data[node]["cluster"]["cluster_id"] is values.MISSED):
                        logger.debug("Cluster data is partially formed and ClusterID not found")
                    else:
                        cluster_id.append(
                           cluster_data[node]["cluster"]["cluster_id"]
                        )

            if cluster_id:
                if len(set(cluster_id)) != 1:
                    logger.warning(
                      "ClusterID assignment NOT unique across "
                      f"the nodes of the cluster: {cluster_id}. "
                      "Possible warning: Check if cluster values "
                      "have been manually tampered with."
                    )

                else:
                    res = cluster_id[0]

            else:
                logger.warning(
                     "ClusterID is not present in Pillar data for "
                     "either of the nodes."
                )

        # Raising error and returning None to handle in `run()`
        except ValueError as exc:
            logger.error(
                "Error in retrieving cluster_id from "
                f"Pillar data: {str(exc)}"
            )

        return res

    def run(self, targets=ALL_MINIONS):
        """cluster_id assignment

        Execution:
        `provisioner cluster_id`
        Takes no mandatory argument as input.
        Run only on primary node.

        """
        try:
            node_role = grains_get(
                "roles",
                local_minion_id()
            )[local_minion_id()]["roles"]            # displays as a list

            cluster_id_from_pillar = self._get_cluster_id()

            if node_role[0] != "primary":
                logger.info(
                     f"Role of current node: '{node_role[0]}'."
                )
                cluster_id_from_setup = self._initial_check(
                                        node_role[0],
                                        cluster_id_from_pillar)

            else:
                logger.debug("This is the Primary node of the cluster.")

                if not cluster_id_from_pillar:
                    logger.debug(
                       "ClusterID not set in pillar data. "
                       "Checking setup file.."
                    )

                # double verification
                cluster_id_from_setup = self._initial_check(
                                        node_role[0],
                                        cluster_id_from_pillar)

                if cluster_id_from_setup == cluster_id_from_pillar:
                    logger.debug(
                      "A unique ClusterID is already set!"
                    )

                elif (cluster_id_from_pillar and
                            cluster_id_from_setup != cluster_id_from_pillar):
                    logger.warning(
                       "Mismatch in cluster_id value between "
                       "setup and pillar data. Setting unique value now.."
                       "\nPossible warning: Check if cluster values "
                       "have been manually tampered with."
                    )

                PillarSet().run(
                    'cluster/cluster_id',
                    f'{cluster_id_from_setup}',
                    targets=ALL_MINIONS
                )

                # Ensure cluster-id file is created in all nodes
                StatesApplier.apply(
                       ['components.provisioner.config.cluster_id',
                        'components.system.config.sync_salt'
                       ],
                       targets=ALL_MINIONS
                )

            return f"cluster_id: {cluster_id_from_setup}"

        except Exception as exc:
            raise ValueError(
                "Failed: Encountered error while setting "
                f"cluster_id to Pillar data: {str(exc)}"
            )