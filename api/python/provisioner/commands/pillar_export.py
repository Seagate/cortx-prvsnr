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
import sys
from pathlib import Path
from collections.abc import Mapping

from ..config import (
    CORTX_CONFIG_DIR,
    CONFSTORE_CLUSTER_CONFIG
)

from ..vendor import attr
from .. import inputs

from . import (
    PillarGet
)

logger = logging.getLogger(__name__)


class RunArgsPillarExportAttrs:
    export_file: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
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
           (type(None), bool, list, int))):
            return str(obj)
        elif isinstance(obj, Mapping):
            return {k: self._convert_to_str(v, repl) for k, v in obj.items()}
        return obj

    def run(self, *args, **kwargs):
        try:
            full_pillar_load = PillarGet.run(self, *args)
            Path(CORTX_CONFIG_DIR).mkdir(exist_ok=True)

            unwanted_keys = ["mine_functions", "provisioner", "glusterfs"]
            for key in full_pillar_load.keys():
                for filter_key in list(full_pillar_load[key].keys()):
                    if filter_key in unwanted_keys:
                        del full_pillar_load[key][filter_key]

            convert_data = self._convert_to_str(full_pillar_load, "")

            if ("--export-file" in sys.argv[2:]):
                file_to_write = kwargs["export_file"]
            else:
                file_to_write = f'{CONFSTORE_CLUSTER_CONFIG}'

            with open(file_to_write, "w") as file_value:
                json.dump(convert_data, file_value)

            logger.info(f"Pillar data exported as JSON to file '{file_to_write}' Successfully.")
            return (f"Pillar data exported as JSON to file '{file_to_write}' Successfully.")

        except Exception as exc:
            raise ValueError(
                  f"Error in translating Pillar data to JSON: {str(exc)}")
