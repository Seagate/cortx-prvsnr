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

from pathlib import Path
import logging

from typing import Union, Optional, List, Dict

from provisioner.vendor import attr
from provisioner import config
from provisioner.attr_gen import attr_ib


logger = logging.getLogger(__name__)


class MiniAPIParams:
    spec: Union[Path, str] = attr_ib(
        'path_exists', cli_spec='mini_api/spec'
    )
    hook: str = attr_ib(
        cli_spec='mini_api/hook',
        validator=attr.validators.in_(config.MiniAPIHooks),
        converter=config.MiniAPIHooks
    )
    flow: Union[config.CortxFlows, str] = attr_ib(
        cli_spec='mini_api/flow',
        validator=attr.validators.in_(config.CortxFlows),
        converter=config.CortxFlows
    )
    level: Union[config.MiniAPILevels, str] = attr_ib(
        cli_spec='mini_api/level',
        validator=attr.validators.in_(config.MiniAPILevels),
        converter=config.MiniAPILevels
    )
    fail_fast: bool = attr_ib(
        cli_spec='mini_api/fail_fast',
        default=False
    )
    sw: Optional[List] = attr_ib(
        cli_spec='mini_api/sw',
        default=None
    )
    ctx_vars: Optional[Dict] = attr_ib(
        cli_spec='mini_api/ctx_vars',
        default=None
    )
    confstore: str = attr_ib(
        cli_spec='mini_api/confstore', default='""'
    )
    normalize: bool = attr_ib(
        cli_spec='mini_api/normalize',
        default=False
    )
