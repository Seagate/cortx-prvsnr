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

# Python API to set unique ClusterID to pillar file

import logging
import uuid
from typing import Type

from .. import inputs
from ..api import grains_get
from ..config import LOCAL_MINION

from provisioner.commands import (
    PillarSet
)
from . import CommandParserFillerMixin

from ..vendor import attr
from provisioner.salt import local_minion_id

logger = logging.getLogger(__name__)

# TODO TEST
@attr.s(auto_attribs=True)
class GetClusterId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsEmpty

    def run(self):
        # return list(function_run(
        #     'grains.get',
        #     fun_args=['cluster_id']
        # ).values())[0]

        PillarGet().run(
            'cluster/cluster_id',
            targets=local_minion_id()
        )[local_minion_id()]


@attr.s(auto_attribs=True)
class SetClusterId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, cluster_id=None):
        """set_cluster_id command execution method.

        Will be executed only on primary node.
        Gets cluster id from pillar data.
        If not present, generates a uuid and sets.

        Execution:
        `provisioner set_cluster_id`
        Takes no mandatory argument as input.

        """
        try:
            node_role = grains_get(
                "roles",
                local_minion_id()
            )[local_minion_id()]["roles"]            # displays as a list

            if node_role[0] != "primary":
                # logger.error(
                #      "Error: ClusterID can be set only in the Primary node "
                #      f"of the cluster. Node role received: '{node_role[0]}'."
                # )
                raise ValueError(
                     "Error: ClusterID can be set only in the Primary node "
                     f"of the cluster. Node role received: '{node_role[0]}'."
                )

            logger.info(
                "Setting Cluster Id on Primary node of the cluster."
            )

            cluster_id_from_grains = grains_get(
                "cluster_id",
                local_minion_id()
            )[local_minion_id()]["cluster_id"]

            cluster_id_from_pillar = PillarGet().run(
                'cluster/cluster_id',
                targets=local_minion_id()
            )[local_minion_id()]
            cluster_id_from_pillar = GetClusterId.run()

            # Check if Cluster ID is set in Grains

            if not cluster_id_from_grains:
                logger.info(
                    "ClusterID is not found in grains data. Generating one.."
                )
                cluster_uuid = str(uuid.uuid4())
                logger.info("Setting the generated ClusterID across all nodes..")

                PillarSet().run(
                    'cluster/cluster_id',
                    f'{cluster_uuid}',
                    targets=local_minion_id()
                )

            elif cluster_id_from_grains and not cluster_id_from_pillar:
                logger.info(
                    "ClusterID is not set in pillar data. Proceeding to set now.."
                )
                PillarSet().run(
                    'cluster/cluster_id',
                    f'{cluster_id_from_grains}',
                    targets=local_minion_id()
                )

            else:
                logger.info(
                    "Bootstrapping completed and ClusterID is already set!"
                )

            logger.info(
                "Success: Unique ClusterID assignment to pillar data."
            )

        except Exception as exc:
            raise ValueError(
                "Failed: Encountered error while setting "
                f"cluster_id to Pillar data: {str(exc)}"
            )
