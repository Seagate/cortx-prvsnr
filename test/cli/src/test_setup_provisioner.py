import os
import pytest
import json
import logging

import test.helper as h

logger = logging.getLogger(__name__)


# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/setup-provisioner"


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


@pytest.fixture(scope='module')
def local_scripts_path(project_path):
    return [
        str(project_path / 'cli/src/setup-provisioner'),
        str(project_path / 'cli/src/functions.sh')
    ]


@pytest.fixture(scope='module')
def post_host_run_hook(localhost, local_scripts_path):
    def f(host, hostname, ssh_config, request):
        host_script_dir = '/tmp'
        for local_path in local_scripts_path:
            localhost.check_output(
                "scp -F {} {} {}:{}".format(
                    ssh_config,
                    local_path,
                    hostname,
                    host_script_dir
                )
            )
    return f


def run_script(host, *args, script_path=DEFAULT_SCRIPT_PATH, trace=False):
    return h.run(
        host, (
            "bash {} {} {} 2>&1"
            .format(
                '-x' if trace else '',
                script_path,
                ' '.join([*args])
            )
        )
    )


# TODO split
@pytest.mark.isolated
def test_setup_provisioner_fail(host):
    ssh_config = '/tmp/ssh_config'
    host.check_output(
        "echo -e 'Host eosnode-1\n\nHost eosnode-2' >{}"
        .format(ssh_config)
    )

    res = run_script(host, "--repo-src some-src")
    assert res.rc == 5
    assert 'Incorrect repo source' in res.stdout

    res = run_script(
        host,
        "--remote eosnode-1"
    )
    assert res.rc == 1
    assert 'eosnode-1 node ssh configuration is not found' in res.stdout

    res = run_script(
        host,
        "--ssh-config {} --remote some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-1 node ssh configuration is not found' in res.stdout

    res = run_script(
        host,
        "--ssh-config {} --remote some-user@".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-1 node ssh configuration is not found' in res.stdout

    # eosnode-2
    res = run_script(
        host,
        "--eosnode-2 eosnode-2"
    )
    assert res.rc == 1
    assert 'eosnode-2 node ssh configuration is not found' in res.stdout

    res = run_script(
        host,
        "--ssh-config {} --eosnode-2 some-hostspec".format(
            ssh_config
        )
    )
    assert res.rc == 1
    assert 'eosnode-2 node ssh configuration is not found' in res.stdout

    res = run_script(
        host,
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
    host, hostname, localhost, ssh_config, remote, project_path, request
):
    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'setup-provisioner'
    else:
        host_project_path = request.getfixturevalue('inject_repo')['host']
        script_path = host_project_path / 'cli' / 'src' / 'setup-provisioner'

    remote = '--remote {}'.format(hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = '' # TODO

    res = run_script(
        localhost if remote else host,
        "{} {} {} --repo-src local --singlenode".format(ssh_config, with_sudo, remote),
        script_path=script_path
    )
    assert res.rc == 0

    # check states listed
    # TODO timeout make sense, not so good - makes test unstable,
    #      also it has some strange behaviour
    for _try in range(2):
        res = host.run('salt eosnode-1 --out json --timeout 10 state.show_top')
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


def check_setup_provisioner_results(host_eosnode1):
    states_expected = [
        "components.{}".format(st) for st in
        ['system', 'sspl', 'eoscore', 'halon', 'misc.build_ssl_cert_rpms', 'ha.haproxy', 'misc.openldap', 's3server']
    ]

    for minion_id in ('eosnode-1', 'eosnode-2'):
        # check states listed
        # TODO timeout make sense, not so good - makes test unstable,
        #      also it has some strange behaviour
        states = []
        for _try in range(2):
            res = host_eosnode1.run(
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
@pytest.mark.hosts(['host_eosnode1', 'host_eosnode2'])
@pytest.mark.inject_ssh_config(['host_eosnode1'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("repo_src", ['local'])
def test_setup_provisioner_cluster(
    host_eosnode1, host_eosnode2, hostname_eosnode1, hostname_eosnode2,
    ssh_config, localhost, remote, repo_src, project_path, request, inject_ssh_config
):
    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'setup-provisioner'
    else:
        # in case of 'local' source inject the whole repository
        if repo_src == 'local':
            host_project_path = request.getfixturevalue('inject_repo')['host_eosnode1']
            script_path = host_project_path / 'cli' / 'src' / 'setup-provisioner'
        # not required otherwise
        else:
            script_path = DEFAULT_SCRIPT_PATH

    remote = '--remote {}'.format(hostname_eosnode1) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config)
    with_sudo = '' # TODO

    res = run_script(
        localhost if remote else host_eosnode1,
        "{} {} {} --eosnode-2 {} --repo-src {}".format(
            ssh_config, with_sudo, remote, hostname_eosnode2, repo_src
        ),
        script_path=script_path
    )
    assert res.rc == 0
    check_setup_provisioner_results(host_eosnode1)


@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.hosts(['host_eosnode1', 'host_eosnode2'])
def test_setup_provisioner_cluster_with_salt_master_host_provided(
    host_eosnode1, hostname_eosnode1, hostname_eosnode2,
    ssh_config, localhost, project_path, host_meta_eosnode1
):
    script_path = project_path / 'cli' / 'src' / 'setup-provisioner'
    salt_server_ip = host_eosnode1.interface(host_meta_eosnode1.iface).addresses[0]

    ssh_config = '--ssh-config {}'.format(ssh_config)
    remote = '--remote {}'.format(hostname_eosnode1)
    with_sudo = '' # TODO

    res = run_script(
        localhost,
        "{} {} {} --eosnode-2 {} --salt-master {} --repo-src local".format(
            ssh_config, with_sudo, remote, hostname_eosnode2,
            salt_server_ip
        ),
        script_path=script_path
    )
    assert res.rc == 0
    check_setup_provisioner_results(host_eosnode1)
