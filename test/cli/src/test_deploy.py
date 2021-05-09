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

import os
import pytest
import logging

logger = logging.getLogger(__name__)

# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/deploy-cortx"


@pytest.fixture(scope='module')
def env_level():
    return 'base'


@pytest.fixture(scope='module')
def script_name():
    return 'deploy-cortx'


# TODO test=True case
# TODO
@pytest.mark.skip(reason='need to make more stable to changes in deploy-cortx')
@pytest.mark.isolated
@pytest.mark.mock_cmds({'': ['salt']})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "singlenode", [True, False], ids=['singlenode', 'cluster']
)
def test_deploy_cortx_commands(
    mhost, mlocalhost, ssh_config, remote, singlenode, mock_hosts, run_script
):
    remote = '--remote {}'.format(mhost.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = ''  # TODO

    res = run_script(
        "{} {} {} {}".format(
            ssh_config, with_sudo, remote, '--singlenode' if singlenode else ''
        ),
        mhost=(mlocalhost if remote else mhost)
    )
    assert res.rc == 0

    if singlenode:
        expected_lines = [
            'SALT-ARGS: srvnode-1 state.apply {}'.format(state)
            for state in [
                'system',
                'ha.haproxy',
                'misc_pkgs.openldap',
                'misc_pkgs.build_ssl_cert_rpms',
                'motr',
                's3server',
                'hare',
                'sspl',
                'csm'
            ]
        ]
    else:
        expected_lines = [
            'SALT-ARGS: srvnode-[1,2] state.apply {}'.format(state)
            for state in ['system', 'ha.haproxy', 'misc_pkgs.openldap']
        ] + [
            'SALT-ARGS: srvnode-1 state.apply misc_pkgs.build_ssl_cert_rpms',  # noqa: E501
            'SALT-ARGS: srvnode-2 state.apply misc_pkgs.build_ssl_cert_rpms'  # noqa: E501
        ] + [
            'SALT-ARGS: srvnode-[1,2] state.apply {}'.format(state)
            for state in ['cortx', 's3server', 'hare', 'sspl', 'csm']
        ]

    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = [
        line for line in res.stdout.split(os.linesep) if 'SALT-ARGS' in line
    ]
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
