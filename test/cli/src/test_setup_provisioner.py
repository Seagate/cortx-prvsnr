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
import yaml
import logging
import functools

import test.helper as h

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_level():
    return 'base'


@pytest.fixture(scope='module')
def script_name():
    return 'setup-provisioner'


@pytest.fixture
def run_script(run_script, tmpdir_function):
    return functools.partial(
        run_script, env=dict(
            LOG_FILE='{}'.format(tmpdir_function / 'setup-provisioner.log')
        )
    )


@pytest.fixture
def install_salt_config_files(project_path):
    def _f(mhost):
        mhost.copy_to_host(
            project_path / 'files/etc/salt',
            h.PRVSNR_REPO_INSTALL_DIR / 'files/etc/salt'
        )
    return _f


# TODO split
@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
def test_setup_provisioner_fail(mhost, run_script):
    ssh_config = '/tmp/ssh_config'
    mhost.check_output(
        "echo -e 'Host srvnode-1\n\nHost srvnode-2' >{}"
        .format(ssh_config)
    )

    res = run_script("--repo-src some-src")
    assert res.rc == 5
    assert 'Incorrect repo source' in res.stdout

    # CLUSTER - REMOTE - CUSTOM SSH - spec for salt-master not in config
    res = run_script(
        "--ssh-config {} --remote some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-1 in ssh-config'
        in res.stdout
    )

    res = run_script(
        "--ssh-config {} --remote some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-1 in ssh-config'
        in res.stdout
    )

    # CLUSTER - REMOTE - CUSTOM SSH - spec for secondary not in config
    res = run_script(
        "--ssh-config {} --remote srvnode-1 --srvnode-2 some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-2 in ssh-config'
        in res.stdout
    )

    res = run_script(
        "--ssh-config {} --remote srvnode-1 --srvnode-2 some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-2 in ssh-config'
        in res.stdout
    )

    # CLUSTER - LOCAL - CUSTOM SSH - spec for secondary not in config
    res = run_script(
        "--ssh-config {} --srvnode-2 some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-2 in ssh-config'
        in res.stdout
    )

    res = run_script(
        "--ssh-config {} --srvnode-2 some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-2 in ssh-config'
        in res.stdout
    )

    # srvnode-2
    # res = run_script(
    #     "--srvnode-2 srvnode-2"
    # )
    # assert res.rc == 1
    # assert (
    #     'Invalid ssh configuration provided for srvnode-2 in ssh-config'
    #     in res.stdout
    # )

    # SINGLENODE - REMOTE - CUSTOM SSH - spec for salt-master not in config
    res = run_script(
        "--singlenode --ssh-config {} --remote some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-1 in ssh-config'
        in res.stdout
    )

    res = run_script(
        "--singlenode --ssh-config {} --remote some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert (
        'Invalid ssh configuration provided for srvnode-1 in ssh-config'
        in res.stdout
    )


# TODO
# - add checks:
#   - network is configured
@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.env_provider('vbox')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_setup_provisioner_singlenode(
    mhost, mlocalhost, ssh_config, remote, run_script
):
    remote = '--remote {}'.format(mhost.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = ''  # TODO

    res = run_script(
        "-v {} {} {} --repo-src local --singlenode".format(
            ssh_config, with_sudo, remote
        ),
        trace=True,
        mhost=(mlocalhost if remote else mhost)
    )
    assert res.rc == 0

    # check states listed
    # TODO timeout make sense, not so good - makes test unstable,
    #      also it has some strange behaviour
    for _try in range(2):
        res = mhost.run(
            'salt srvnode-1 --out json --timeout 10 state.show_top'
        )
        if res.rc == 0:
            break
    assert res.rc == 0
    output = json.loads(res.stdout)

    top_sls_content = mhost.check_output(
        'cat {}'.format(h.PRVSNR_REPO_INSTALL_DIR / 'srv/top.sls')
    )
    top_sls_dict = yaml.safe_load(top_sls_content)
    states_expected = top_sls_dict['base']['*']

    assert output == {
        'srvnode-1': {
            'base': states_expected
        }
    }


def check_setup_provisioner_results(mhostsrvnode1):
    top_sls_content = mhostsrvnode1.check_output(
        'cat {}'.format(h.PRVSNR_REPO_INSTALL_DIR / 'srv/top.sls')
    )
    top_sls_dict = yaml.safe_load(top_sls_content)
    states_expected = top_sls_dict['base']['*']

    for minion_id in ('srvnode-1', 'srvnode-2'):
        # check states listed
        # TODO timeout make sense, not so good - makes test unstable,
        #      also it has some strange behaviour
        states = []
        for _try in range(2):
            res = mhostsrvnode1.run(
                "salt '*' --out json --static --timeout 10 state.show_top"
            )
            if res.rc == 0:
                output = json.loads(res.stdout)
                states = output[minion_id].get('base', [])
                if states:
                    break
        assert states == states_expected


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.env_provider('vbox')
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
@pytest.mark.inject_ssh_config(['srvnode1'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("repo_src", ['local', 'rpm', 'github'])
def test_setup_provisioner_cluster(
    mhostsrvnode1, mhostsrvnode2, ssh_config, mlocalhost,
    remote, repo_src, inject_ssh_config, run_script
):
    remote = '--remote {}'.format(mhostsrvnode1.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config)
    with_sudo = ''  # TODO

    res = run_script(
        "-v {} {} {} --srvnode-2 {} --repo-src {}".format(
            ssh_config, with_sudo, remote, mhostsrvnode2.hostname, repo_src
        ),
        mhost=(mlocalhost if remote else mhostsrvnode1)
    )
    assert res.rc == 0
    check_setup_provisioner_results(mhostsrvnode1)


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.env_provider('vbox')
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
def test_setup_provisioner_cluster_with_salt_master_host_provided(
    mhostsrvnode1, mhostsrvnode2, ssh_config, mlocalhost, run_script
):
    salt_server_ip = mhostsrvnode1.host.interface(
        mhostsrvnode1.interface
    ).addresses[0]

    ssh_config = '--ssh-config {}'.format(ssh_config)
    remote = '--remote {}'.format(mhostsrvnode1.hostname)
    with_sudo = ''  # TODO

    res = run_script(
        "-v {} {} {} --srvnode-2 {} --salt-master {} --repo-src local".format(
            ssh_config, with_sudo, remote, mhostsrvnode2.hostname,
            salt_server_ip
        ),
        mhost=mlocalhost,
    )
    assert res.rc == 0
    check_setup_provisioner_results(mhostsrvnode1)
