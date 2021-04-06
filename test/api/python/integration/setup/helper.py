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


class RunT(Enum):
    """Modes of setup run"""

    REMOTE_CLI = 'remote_cli'       # logic is run on the host system via CLI
    REMOTE_API = 'remote_api'       # via API
    ONTARGET_CLI = 'ontarget_cli'   # logic is run on a target system via CLI
    # ONTARGET_API = 'ontarget_api' # via API


class ScaleFactorT(Enum):
    """Types of setup relative to nodes number"""

    NODE1 = 1
    NODE3 = 3
    NODE6 = 6
    SINGLE = 1  # an alias


class SourceT(Enum):
    """Types of sources for setup"""

    LOCAL = 'local'
    ISO = 'iso'


def create_hosts(request, hosts_num) -> List[HostMeta]:
    request.applymarker(
        pytest.mark.hosts(
            [f'srvnode{i}' for i in range(1, hosts_num + 1)]
        )
    )

    return [
        request.getfixturevalue(f'mhostsrvnode{i}')
        for i in range(1, hosts_num + 1)
    ]


def set_root_passwd(mhosts: List[HostMeta], passwd: str):
    for mhost in mhosts:
        mhost.check_output(f'echo {passwd} | passwd --stdin root')
