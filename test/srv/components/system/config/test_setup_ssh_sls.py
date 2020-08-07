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

import os
import pytest
import json

import logging

from test.helper import PRVSNR_REPO_INSTALL_DIR

logger = logging.getLogger(__name__)

# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
@pytest.mark.skip(reason="EOS-4907")
def test_setup_ssh_known_hosts(
    mhostsrvnode1, eos_hosts, configure_salt, accept_salt_keys
):
    minion_id = eos_hosts['srvnode1']['minion_id']

    mhostsrvnode1.check_output(
        "salt '{}' state.apply components.system.config.setup_ssh".format(
            minion_id
        )
    )

    output = mhostsrvnode1.check_output('salt-call --local --out json config.get master')
    master_host = json.loads(output)['local']

    # TODO checks for the keys' types
    mhostsrvnode1.check_output('ssh-keygen -F {}'.format(minion_id))
    mhostsrvnode1.check_output('ssh-keygen -F {}'.format(master_host))
