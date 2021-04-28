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
from .. import inputs
from provisioner.api import grains_get

from provisioner.commands import (
     PillarGet,
     PillarSet
)
from provisioner.config import (
     CLUSTER_ID_FILE,
     ALL_MINIONS
)
from provisioner.salt import local_minion_id
from provisioner.utils import run_subprocess_cmd
from provisioner.vendor import attr

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ClusterId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def _initial_check(self):
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
                logger.info("ClusterID file does not exist. Creating now..")

                # TODO: Rid of this step once we move out of grains data
                cluster_id = grains_get(
                    "cluster_id",
                    local_minion_id()
                )[local_minion_id()]["cluster_id"]

                if not cluster_id:
                    logger.info(
                        "ClusterID is not found in grains data. Generating one.."
                    )
                    cluster_id = str(uuid.uuid4())

                with open(CLUSTER_ID_FILE, "w+") as file_value:
                    file_value.write(cluster_id)

                # TODO: check if there's a better way to make file immutable
                _cmd = f"chattr +i {CLUSTER_ID_FILE} && lsattr {CLUSTER_ID_FILE}"
                run_subprocess_cmd([_cmd], check=False, shell=True).stdout

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
            cluster_id = []

            for node in cluster_data:
                if "cluster_id" in cluster_data[node]["cluster"]:
                    cluster_id.append(
                      cluster_data[node]["cluster"]["cluster_id"]
                    )
                else:
                    logger.error(
                      "ClusterID is not present in Pillar data for "
                      "either of the nodes."
                    )

            if len(set(cluster_id)) != 1:
                logger.error(
                  "ERROR: ClusterID assignment not unique across "
                  f"the nodes of the cluster: {cluster_id}. "
                  "Possible warning: Cluster values have been manually tampered with."
                )

            res = cluster_id[0]

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
        Executed only on primary node.

        """
        try:
            node_role = grains_get(
                "roles",
                local_minion_id()
            )[local_minion_id()]["roles"]            # displays as a list

            if node_role[0] != "primary":
                raise ValueError(
                  "Error: ClusterID can be set only in the Primary node "
                  f"of the cluster. Node role received: '{node_role[0]}'."
                )

            logger.info("This is the Primary node of the cluster.")

            cluster_id_from_setup = self._initial_check()

            # double verification
            cluster_id_from_pillar = self._get_cluster_id()

            if not cluster_id_from_pillar:
                logger.info(
                   "ClusterID not set in pillar data. Setting now.."
                )

            elif cluster_id_from_setup != cluster_id_from_pillar:
                logger.info(
                   "Mismatch in cluster_id value between "
                   "setup and pillar data. Setting unique value now.."
                )

            PillarSet().run(
                'cluster/cluster_id',
                f'{cluster_id_from_setup}',
                targets=targets
            )

            logger.info(
                "Bootstrapping completed and ClusterID is already set!"
            )

            return "Success: Unique ClusterID assignment to pillar data."

        except Exception as exc:
            raise ValueError(
                "Failed: Encountered error while setting "
                f"cluster_id to Pillar data: {str(exc)}"
            )
