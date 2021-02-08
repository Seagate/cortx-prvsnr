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

import logging
import json

from pathlib import Path
from collections.abc import Mapping

from ..config import (
    CORTX_CONFIG_DIR,
    CONFSTORE_CLUSTER_CONFIG
)

from provisioner.api import grains_get
from provisioner.commands import PillarGet
from provisioner.inputs import METADATA_ARGPARSER
from provisioner.salt import local_minion_id
from provisioner.vendor import attr

logger = logging.getLogger(__name__)


class RunArgsPillarExportAttrs:
    export_file: str = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': "output file to export JSON format of pillar data"
            }
        },
        default=CONFSTORE_CLUSTER_CONFIG
    )


@attr.s(auto_attribs=True)
class RunArgsPillarExport:
    export_file: str = RunArgsPillarExportAttrs.export_file

    def __attrs_post_init__(self):
        pass


@attr.s(auto_attribs=True)
class PillarExport(PillarGet):
    _run_args_type = RunArgsPillarExport

    def _convert_to_str(self, obj, repl=''):
        """
        Method to address ConfStore LIMITATION.

        Currently, ConfStore accepts ONLY string values.
        This can be commented when limitation is addressed.

        Converts all values (arrays, null, bool, int) to string

        """
        if (isinstance(obj,
           (type(None), bool, int))):
            return str(obj)
        elif isinstance(obj, Mapping):
            return {k: self._convert_to_str(v, repl) for k, v in obj.items()}
        return obj

    def run(
        self,
        *args,
        **kwargs
    ):
        """pillar_export command execution method.

        Keyword arguments:
        *args: Pillar path in <root_node>/child_node format.
        (default: all pillar data)
        **kwargs: accepts the following keys:
            export_file: Output file for pillar dump
        """

        try:
            full_pillar_load = PillarGet().run(
                *args,
                targets=local_minion_id()
            )[local_minion_id()]

            # Knock off the unwanted keys
            unwanted_keys = ["mine_functions", "provisioner", "glusterfs"]
            for key in full_pillar_load.copy().keys():
                if key in unwanted_keys:
                    del full_pillar_load[key]

            ip4_interfaces = grains_get(
                "ip4_interfaces",
                targets=local_minion_id()
            )[local_minion_id()]["ip4_interfaces"]

            # Update interface IPs
            # Public Management Interface
            mgmt_if_public = (
                "mgmt0" if "mgmt0" in ip4_interfaces
                else full_pillar_load["cluster"] \
                    [local_minion_id()] \
                    ["network"] \
                    ["mgmt"] \
                    ["interfaces"][0]
            )
            full_pillar_load["cluster"] \
                [local_minion_id()] \
                ["network"] \
                ["mgmt"] \
                ["public_ip"] = ip4_interfaces[mgmt_if_public][0]

            # Public Data Interface
            data_if_public = (
                "data0" if "data0" in ip4_interfaces
                else full_pillar_load["cluster"] \
                    [local_minion_id()] \
                    ["network"] \
                    ["data"] \
                    ["public_interfaces"][0]
            )
            full_pillar_load["cluster"] \
                [local_minion_id()] \
                ["network"] \
                ["data"] \
                ["public_ip"] = ip4_interfaces[data_if_public][0]

            # Private Data Interface
            data_if_private = (
                "data0" if "data0" in ip4_interfaces
                else full_pillar_load["cluster"] \
                    [local_minion_id()] \
                    ["network"] \
                    ["data"] \
                    ["private_interfaces"][0]
            )
            full_pillar_load["cluster"] \
                [local_minion_id()] \
                ["network"] \
                ["data"] \
                ["private_ip"] = ip4_interfaces[data_if_private][0]

            convert_data = self._convert_to_str(full_pillar_load, "")

            pillar_dump_file = (
                kwargs["export_file"] if "export_file" in kwargs
                else CORTX_CONFIG_DIR
            )

            Path(CORTX_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
            with open(pillar_dump_file, "w") as file_value:
                json.dump(convert_data, file_value)

            logger.info("SUCCESS: Pillar data exported as JSON to file "
                f"'{pillar_dump_file}'."
            )

        except Exception as exc:
            raise ValueError(
                  f"Error in translating Pillar data to JSON: {str(exc)}")
