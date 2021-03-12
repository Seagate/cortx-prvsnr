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
import json

import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_level():
    return 'salt-installed'


# TODO might makes sense to verify for cluster case as well
@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
def test_mine_functions_primary_host_keys(
    mhostsrvnode1, cortx_hosts, configure_salt, accept_salt_keys
):
    def _make_data_comparable(data):
        data = [
            {k: v for k, v in litem.items() if k != 'hostname'}
            for litem in data
        ]
        return sorted(data, key=lambda k: k['enc'])

    mine_function_alias = 'primary_host_keys'
    minion_id = cortx_hosts['srvnode1']['minion_id']

    output = mhostsrvnode1.check_output(
        "salt '{}' --out json mine.get 'roles:primary' '{}' grain".format(
            minion_id, mine_function_alias
        )
    )
    mined = json.loads(output)[minion_id]
    assert [minion_id] == list(mined.keys())
    mined = _make_data_comparable(mined[minion_id])

    output = mhostsrvnode1.check_output(
        "salt '{}' --out json ssh.recv_known_host_entries 127.0.0.1".format(
            minion_id
        )
    )
    expected = _make_data_comparable(json.loads(output)[minion_id])

    assert expected == mined
