import os
import pytest
import json
import logging

logger = logging.getLogger(__name__)

# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/deploy-eos"


@pytest.fixture(scope='module')
def env_level():
    return 'base'


@pytest.fixture(scope='module')
def script_name():
    return 'deploy-eos'


# TODO test=True case
# TODO
@pytest.mark.skip(reason='need to make more stable to changes in deploy-eos')
@pytest.mark.isolated
@pytest.mark.mock_cmds({'': ['salt']})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("singlenode", [True, False], ids=['singlenode', 'cluster'])
def test_deploy_eos_commands(
    mhost, mlocalhost, ssh_config, remote, singlenode, mock_hosts, run_script
):
    remote = '--remote {}'.format(mhost.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = '' # TODO

    res = run_script(
        "{} {} {} {}".format(
            ssh_config, with_sudo, remote, '--singlenode' if singlenode else ''
        ),
        mhost=(mlocalhost if remote else mhost)
    )
    assert res.rc == 0

    if singlenode:
        expected_lines = [
            'SALT-ARGS: eosnode-1 state.apply components.{}'.format(state)
            for state in [
                'system',
                'ha.haproxy',
                'misc_pkgs.openldap',
                'misc_pkgs.build_ssl_cert_rpms',
                'eoscore',
                's3server',
                'hare',
                'sspl',
                'csm'
            ]
        ]
    else:
        expected_lines = [
            'SALT-ARGS: eosnode-[1,2] state.apply components.{}'.format(state)
            for state in ['system', 'ha.haproxy', 'misc_pkgs.openldap']
        ] + [
            'SALT-ARGS: eosnode-1 state.apply components.misc_pkgs.build_ssl_cert_rpms',
            'SALT-ARGS: eosnode-2 state.apply components.misc_pkgs.build_ssl_cert_rpms'
        ] + [
            'SALT-ARGS: eosnode-[1,2] state.apply components.{}'.format(state)
            for state in ['eoscore', 's3server', 'hare', 'sspl', 'csm']
        ]

    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = [
        line for line in res.stdout.split(os.linesep) if 'SALT-ARGS' in line
    ]
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
