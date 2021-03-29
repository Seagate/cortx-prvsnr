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


@pytest.mark.debug
def test_fail(test_level, test_topic):
    pytest.fail()

@pytest.mark.debug
def test_pass(test_level, test_topic):
    pass




@pytest.fixture
def env_provider():
    return 'docker'


@pytest.fixture
def hosts_spec(hosts_spec, hosts, tmpdir_function, request):
    res = deepcopy(hosts_spec)
    for host in hosts:
        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']
        docker_settings['privileged'] = True

        if not request.config.getoption("no_docker_mount_glusterfs"):
            host_glusterfs = tmpdir_function / host / 'srv/glusterfs'
            host_glusterfs.mkdir(parents=True)

            docker_settings['volumes'][str(host_glusterfs)] = {
                'bind': '/srv/glusterfs', 'mode': 'rw'
            }

        if request.config.getoption("docker_mount_dev"):
            docker_settings['volumes']['/dev'] = {
                'bind': '/dev', 'mode': 'ro'
            }
    return res


@pytest.mark.isolated
@pytest.mark.timeout(86400)  # one day timeout
def test_build_setup_env(
    request, root_passwd, nodes_num, ssh_config, env_provider,
    ask_proceed
):
    request.applymarker(
        pytest.mark.env_level(
            request.config.getoption("env_level") or 'utils'
        )
    )

    request.applymarker(
        pytest.mark.hosts([f'srvnode{i}' for i in range(1, nodes_num + 1)])
    )

    mhosts = [
        request.getfixturevalue(f'mhostsrvnode{i}')
        for i in range(1, nodes_num + 1)
    ]

    for mhost in mhosts:
        mhost.check_output(f'echo {root_passwd} | passwd --stdin root')

        if env_provider == 'vbox':
            mhost.remote.cmd(
               'snapshot', 'save', mhost.remote.name, 'initial --force'
            )
        elif env_provider == 'docker':
            mhost.check_output('touch /etc/fstab')

    print(ssh_config.read_text())
    print(f'Path to config: {ssh_config}')

    ask_proceed()
