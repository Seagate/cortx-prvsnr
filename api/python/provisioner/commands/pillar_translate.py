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

from ._basic import RunArgs, RunArgsBase

from ..config import (
    ALL_MINIONS,
    CORTX_CONFIG_DIR,
    CONFSTORE_CLUSTER_CONFIG
)

from ..vendor import attr

from . import (
    PillarGet
)

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsPillarTranslate(RunArgsBase):
    local: bool = RunArgs.local


# Method to address ConfStore LIMITATION on accepting ONLY string values
# Can be commented when the bug is addressed.

# Converts all values(null, bool, int) to string

def convert_to_str(obj, repl=''):
    if isinstance(obj, type(None)):
        return str(obj)
    elif isinstance(obj, bool):
        return str(obj)
    elif isinstance(obj, int):
        return str(obj)
    elif isinstance(obj, Mapping):
        return {k: convert_to_str(v, repl) for k, v in obj.items()}
    return obj


@attr.s(auto_attribs=True)
class PillarTranslate(PillarGet):
    _run_args_type = RunArgsPillarTranslate

    def run(
        self, *args, targets: str = ALL_MINIONS, local: bool = False,
        **kwargs
    ):
        full_pillar_load = PillarGet.run(self, *args, **kwargs)
        Path(CORTX_CONFIG_DIR).mkdir(exist_ok=True)

        unwanted_keys = ["mine_functions", "provisioner", "glusterfs"]

        for key in full_pillar_load.keys():
            for filter_key in list(full_pillar_load[key].keys()):
                if filter_key in unwanted_keys:
                    del full_pillar_load[key][filter_key]

        convert_data = convert_to_str(full_pillar_load)
        resp_dumped = json.dumps(convert_data, indent=4, sort_keys=True)
        CONFSTORE_CLUSTER_CONFIG.write_text(resp_dumped)

        return resp_dumped
