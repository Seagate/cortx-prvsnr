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

import pytest
from typing import List
from enum import Enum


from test.conftest import HostMeta

from test.testapi import defs


class RunT(Enum):
    """Modes of setup run"""

    REMOTE_CLI = 'remote_cli'       # logic is run on the host system via CLI
    REMOTE_API = 'remote_api'       # via API
    ONTARGET_CLI = 'ontarget_cli'   # logic is run on a target system via CLI
    # ONTARGET_API = 'ontarget_api' # via API

ScaleFactorT = defs.ScaleFactorT


class SourceT(Enum):
    """Types of sources for setup"""

    LOCAL = 'local'
    ISO = 'iso'
