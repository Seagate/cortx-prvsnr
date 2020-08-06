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
import json

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_level():
    return 'salt-installed'


# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
@pytest.mark.env_level('salt-installed')
def test_mine_functions_primary_host_keys(
    mhosteosnode1, eos_hosts, configure_salt, accept_salt_keys
):
    def _make_data_comparable(data):
        data = [
            {k: v for k, v in litem.items() if k != 'hostname'}
            for litem in data
        ]
        return sorted(data, key=lambda k: k['enc'])

    mine_function_alias = 'primary_host_keys'
    minion_id = eos_hosts['eosnode1']['minion_id']

    output = mhosteosnode1.check_output(
        "salt '{}' --out json mine.get 'roles:primary' '{}' grain".format(
            minion_id, mine_function_alias
        )
    )
    mined = json.loads(output)[minion_id]
    assert [minion_id] == list(mined.keys())
    mined = _make_data_comparable(mined[minion_id])

    output = mhosteosnode1.check_output(
        "salt '{}' --out json ssh.recv_known_host_entries 127.0.0.1".format(
            minion_id
        )
    )
    expected = _make_data_comparable(json.loads(output)[minion_id])

    assert expected == mined
