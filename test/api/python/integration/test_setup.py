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
from collections import defaultdict
from copy import deepcopy

logger = logging.getLogger(__name__)


@pytest.fixture
def env_provider():
    return 'docker'


@pytest.fixture
def hosts_spec(hosts_spec, hosts, tmpdir_function):
    res = deepcopy(hosts_spec)
    for host in hosts:
        host_glusterfs = tmpdir_function / host / 'srv/glusterfs'
        host_glusterfs.mkdir(parents=True)

        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']
        docker_settings['privileged'] = True
        docker_settings['volumes'][str(host_glusterfs)] = {
            # '/dev': {'bind': '/dev', 'mode': 'ro'},
            'bind': '/srv/glusterfs', 'mode': 'rw'
        }
    return res

@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
def test_setup_cluster(
    mhostsrvnode1, mhostsrvnode2, ssh_config, env_provider
):
    mhostsrvnode1.check_output('echo root | passwd --stdin root')
    mhostsrvnode2.check_output('echo root | passwd --stdin root')
    if env_provider == 'vbox':
        for mhost in (mhostsrvnode1, mhostsrvnode2):
            mhost.remote.cmd(
                'snapshot', 'save', mhost.remote.name, 'initial --force'
            )
    print(ssh_config.read_text())
    pass
