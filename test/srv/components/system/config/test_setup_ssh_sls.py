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


# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
@pytest.mark.skip(reason="EOS-4907")
def test_setup_ssh_known_hosts(
    mhostsrvnode1, cortx_hosts, configure_salt, accept_salt_keys
):
    minion_id = cortx_hosts['srvnode1']['minion_id']

    mhostsrvnode1.check_output(
        "salt '{}' state.apply components.system.config.setup_ssh".format(
            minion_id
        )
    )

    output = mhostsrvnode1.check_output(
        'salt-call --local --out json config.get master'
    )
    primary_host = json.loads(output)['local']

    # TODO checks for the keys' types
    mhostsrvnode1.check_output('ssh-keygen -F {}'.format(minion_id))
    mhostsrvnode1.check_output('ssh-keygen -F {}'.format(primary_host))
