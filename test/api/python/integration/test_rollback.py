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
import logging

from test.helper import install_provisioner_api

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_yum_rollback_manager(
    mhostsrvnode1, run_test, cortx_hosts
):
    install_provisioner_api(mhostsrvnode1)
    run_test(mhostsrvnode1, env={
        'TEST_MINION_ID': cortx_hosts['srvnode1']['minion_id']
    })
