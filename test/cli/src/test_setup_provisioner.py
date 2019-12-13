import os
import pytest
import json
import yaml
import logging

import test.helper as h

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


@pytest.fixture(scope='module')
def script_name():
    return 'setup-provisioner'


# TODO split
@pytest.mark.isolated
def test_setup_provisioner_fail(mhost, run_script):
    ssh_config = '/tmp/ssh_config'
    mhost.check_output(
        "echo -e 'Host eosnode-1\n\nHost eosnode-2' >{}"
        .format(ssh_config)
    )

    res = run_script("--repo-src some-src")
    assert res.rc == 5
    assert 'Incorrect repo source' in res.stdout

    res = run_script("--remote eosnode-1")
    assert res.rc == 1
    assert 'eosnode-1 node ssh configuration is not found' in res.stdout

    res = run_script(
        "--ssh-config {} --remote some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-1 node ssh configuration is not found' in res.stdout

    res = run_script(
        "--ssh-config {} --remote some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-1 node ssh configuration is not found' in res.stdout

    # eosnode-2
    res = run_script(
        "--eosnode-2 eosnode-2"
    )
    assert res.rc == 1
    assert 'eosnode-2 node ssh configuration is not found' in res.stdout

    res = run_script(
        "--ssh-config {} --eosnode-2 some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-2 node ssh configuration is not found' in res.stdout

    res = run_script(
        "--ssh-config {} --eosnode-2 some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-2 node ssh configuration is not found' in res.stdout


# TODO
# - add checks:
#   - network is configured
@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_setup_provisioner_singlenode(
    mhost, mlocalhost, ssh_config, remote, run_script
):
    remote = '--remote {}'.format(mhost.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = '' # TODO

    res = run_script(
        "{} {} {} --repo-src local --singlenode".format(ssh_config, with_sudo, remote),
        mhost=(mlocalhost if remote else mhost)
    )
    assert res.rc == 0

    # check states listed
    # TODO timeout make sense, not so good - makes test unstable,
    #      also it has some strange behaviour
    for _try in range(2):
        res = mhost.run('salt eosnode-1 --out json --timeout 10 state.show_top')
        if res.rc == 0:
            break

    assert res.rc == 0

    output = json.loads(res.stdout)
    expected = [
        "components.{}".format(st) for st in
        ['system', 'sspl', 'eoscore', 'halon', 'misc.build_ssl_cert_rpms', 'ha.haproxy', 'misc.openldap', 's3server']
    ]
    assert output == {
        'eosnode-1': {
            'base': expected
        }
    }


def check_setup_provisioner_results(mhosteosnode1):
    states_expected = [
        "components.{}".format(st) for st in
        ['system', 'sspl', 'eoscore', 'halon', 'misc.build_ssl_cert_rpms', 'ha.haproxy', 'misc.openldap', 's3server']
    ]
    top_sls_content = mhosteosnode1.check_output(
        'cat {}'.format(h.PRVSNR_REPO_INSTALL_DIR / 'srv/top.sls')
    )
    top_sls_dict = yaml.safe_load(top_sls_content)
    states_expected = top_sls_dict['base']['*']

    for minion_id in ('eosnode-1', 'eosnode-2'):
        # check states listed
        # TODO timeout make sense, not so good - makes test unstable,
        #      also it has some strange behaviour
        states = []
        for _try in range(2):
            res = mhosteosnode1.run(
                "salt '*' --out json --static --timeout 10 state.show_top"
            )
            if res.rc == 0:
                output = json.loads(res.stdout)
                states = output[minion_id].get('base', [])
                if states:
                    break
        assert states == states_expected


@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.hosts(['eosnode1', 'eosnode2'])
@pytest.mark.inject_ssh_config(['eosnode1'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("repo_src", ['local', 'rpm', 'gitlab'])
def test_setup_provisioner_cluster(
    mhosteosnode1, mhosteosnode2, ssh_config, mlocalhost,
    remote, repo_src, inject_ssh_config, run_script
):
    remote = '--remote {}'.format(mhosteosnode1.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config)
    with_sudo = '' # TODO

    res = run_script(
        "{} {} {} --eosnode-2 {} --repo-src {}".format(
            ssh_config, with_sudo, remote, mhosteosnode2.hostname, repo_src
        ),
        mhost=(mlocalhost if remote else mhosteosnode1)
    )
    assert res.rc == 0
    check_setup_provisioner_results(mhosteosnode1)


@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.hosts(['eosnode1', 'eosnode2'])
def test_setup_provisioner_cluster_with_salt_master_host_provided(
    mhosteosnode1, mhosteosnode2, ssh_config, mlocalhost, run_script
):
    salt_server_ip = mhosteosnode1.host.interface(
        mhosteosnode1.iface
    ).addresses[0]

    ssh_config = '--ssh-config {}'.format(ssh_config)
    remote = '--remote {}'.format(mhosteosnode1.hostname)
    with_sudo = '' # TODO

    res = run_script(
        "{} {} {} --eosnode-2 {} --salt-master {} --repo-src local".format(
            ssh_config, with_sudo, remote, mhosteosnode2.hostname,
            salt_server_ip
        ),
        mhost=mlocalhost,
    )
    assert res.rc == 0
    check_setup_provisioner_results(mhosteosnode1)
