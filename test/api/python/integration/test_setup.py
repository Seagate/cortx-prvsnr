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

import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def env_provider():
    return 'docker'


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.hosts(['srvnode1', 'srvnode2', 'srvnode3'])
def test_setup_cluster(
    mhostsrvnode1, mhostsrvnode2, ssh_config
):
    mhostsrvnode1.check_output('echo root | passwd --stdin root')
    mhostsrvnode2.check_output('echo root | passwd --stdin root')
    pass
