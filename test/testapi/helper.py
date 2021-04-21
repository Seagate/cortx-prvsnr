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
from typing import List

import pytest

logger = logging.getLogger(__name__)


def create_hosts(request, hosts_num):  # -> List[HostMeta]:
    request.applymarker(
        pytest.mark.hosts(
            [f'srvnode{i}' for i in range(1, hosts_num + 1)]
        )
    )

    return [
        request.getfixturevalue(f'mhostsrvnode{i}')
        for i in range(1, hosts_num + 1)
    ]


# def set_root_passwd(mhosts: List[HostMeta], passwd: str):
def set_root_passwd(mhosts: List, passwd: str):
    for mhost in mhosts:
        mhost.check_output(f'echo {passwd} | passwd --stdin root')
