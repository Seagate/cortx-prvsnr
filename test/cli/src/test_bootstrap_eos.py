import os
import pytest
import json
import logging

logger = logging.getLogger(__name__)

# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/bootstrap-eos"


@pytest.fixture(scope='module')
def env_level():
    return 'base'


@pytest.fixture(scope='module')
def script_name():
    return 'bootstrap-eos'


# isolated is required since parametrization is used
@pytest.mark.skip('not maintained')
@pytest.mark.isolated
@pytest.mark.mock_cmds({'': ['salt']})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("singlenode", [True, False], ids=['singlenode', 'cluster'])
def test_bootstrap_eos_commands(
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

    eosnode_1_line = "SALT-ARGS: srvnode-1 state.apply components.post_setup"
    eosnode_2_line = "SALT-ARGS: srvnode-2 state.apply components.post_setup"

    if singlenode:
        expected_lines = [
            eosnode_1_line
        ]
    else:
        expected_lines = [
            eosnode_2_line,
            eosnode_1_line
        ]

    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = [
        line for line in res.stdout.split(os.linesep) if 'SALT-ARGS' in line
    ]
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
