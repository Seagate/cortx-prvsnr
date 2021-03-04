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
from typing import Type

from .. import (
    inputs,
    config
)
from ..config import LOCAL_MINION

from ..paths import (
    USER_SHARED_PILLAR
)

from ..utils import (
    load_yaml,
    dump_yaml
)
from . import (
    CommandParserFillerMixin
)
from ..vendor import attr
# from provisioner.api import grains_get

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SetClusterId(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, targets=LOCAL_MINION):
        """set_cluster_id command execution method.

        Checks for cluster id in common cluster file.
        If not present, generates an id and sets.

        Execution:
        `provisioner set_cluster_id`
        Takes no mandatory argument as input.

        """
        setup_location = config.profile_base_dir().parent
        for setup_file_name in setup_location.iterdir():
            setup_name = str(setup_file_name)
            paths = config.profile_paths(
                    config.profile_base_dir(
                    setup_location, setup_name))

            all_minions_dir = (
                paths['salt_fileroot_dir'] / "provisioner/files/minions/all"
            )
            cluster_id_path = all_minions_dir / 'cluster_id'

            if cluster_id_path.exists():
                logger.info("Bootstrapping done, "
                            "proceeding to set ClusterID to pillar file")
                try:
                    cluster_uuid = load_yaml(cluster_id_path)['cluster_id']

                    cluster_pillar_file = (
                                     f"{USER_SHARED_PILLAR._all_hosts_dir}/"
                                     f"{USER_SHARED_PILLAR._prefix}"
                                     "cluster.sls"
                                     )
                    cluster_content = load_yaml(cluster_pillar_file)

                    if cluster_content["cluster"]["cluster_id"]:
                        logger.info("ClusterID is already set!")
                    else:
                        cluster_content["cluster"]["cluster_id"] = cluster_uuid
                        dump_yaml(cluster_pillar_file, cluster_content)

                    logger.info(
                        "Success: Unique ClusterID assignment after bootstrap process."
                    )

                except Exception as exc:
                    raise ValueError(
                        "Failed: Encountered error while setting "
                        f"cluster_id to Pillar data: {str(exc)}"
                    )

            else:
                logger.error("Error: A unique ClusterID can be set only AFTER "
                             "the Provisioner bootstrap process. "
                             "For bootstrapping, execute the 'setup_provisioner' API.")
                raise ValueError(
                    "Error: ClusterID can only be set AFTER the bootstrap process. "
                    "For Provisioner bootstrapping, please execute the command: 'setup_provisioner'."
                )
