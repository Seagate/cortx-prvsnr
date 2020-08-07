#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import pytest
import logging

from test.helper import install_provisioner_api

logger = logging.getLogger(__name__)


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_yum_rollback_manager(
    mhostsrvnode1, run_test, eos_hosts
):
    install_provisioner_api(mhostsrvnode1)
    run_test(mhostsrvnode1, env={
        'TEST_MINION_ID': eos_hosts['srvnode1']['minion_id']
    })
