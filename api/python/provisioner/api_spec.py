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

import logging

from typing import Dict
from pathlib import Path

from .config import API_SPEC_PATH, PARAMS_SPEC_PATH
from .utils import load_yaml
from provisioner import param

MODULE_DIR = Path(__file__).resolve().parent

PILLAR_PATH_KEY = '_path'
PARAM_TYPE_KEY = '_type'

logger = logging.getLogger(__name__)


def process_param_spec(  # noqa: C901 FIXME
    spec: Dict, parent: Path = None, path: Path = None, dest: dict = None
):
    if dest is None:
        dest = {}

    if parent is None:
        parent = Path()

    for key, value in spec.items():
        if key == PILLAR_PATH_KEY:
            path = Path(value)
        else:
            pname = str(parent / key)
            if type(value) is dict:
                _type = getattr(param, value.pop(PARAM_TYPE_KEY, 'Param'))
                if _type is param.Param:
                    process_param_spec(value, parent / key, path, dest=dest)
                else:
                    if PILLAR_PATH_KEY not in value:
                        value[PILLAR_PATH_KEY] = path
                    dest[pname] = _type.from_spec(pname, **value)
            elif type(value) is str:
                if path is None:
                    logger.error(
                        "Pillar path for {} is unknown"
                        .format(pname)
                    )
                    raise ValueError(
                        'pillar path for {} is unknown'.format(pname)
                    )
                if pname in dest:
                    logger.error("Duplicate entry {}".format(pname))
                    raise ValueError('duplicate entry {}'.format(pname))
                dest[pname] = param.Param(pname, (value, path))
            else:
                logger.error("Failed to update {}".format(type(value)))
                raise TypeError('{}'.format(type(value)))

    return dest


param_spec = process_param_spec(load_yaml(PARAMS_SPEC_PATH))
api_spec = load_yaml(API_SPEC_PATH)
