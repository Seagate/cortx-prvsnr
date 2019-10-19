import os
import pytest
import json
import logging

logger = logging.getLogger(__name__)

# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/bootstrap-eos"

@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


@pytest.fixture(scope='module')
def local_scripts_path(project_path):
    return [
        str(project_path / 'cli/src/bootstrap-eos'),
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
    host = _host if host is None else host
    res = None
    try:
        res = host.run(
            "bash {} {} {} 2>&1"
            .format(
                '-x' if trace else '',
                script_path,
                ' '.join([*args])
            )
        )
    finally:
        if res is not None:
            for line in res.stdout.split(os.linesep):
                logger.debug(line)

    return res


# isolated is required since parametrization is used
@pytest.mark.isolated
@pytest.mark.mock_cmds(['salt'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("singlenode", [True, False], ids=['singlenode', 'cluster'])
def test_bootstrap_eos_commands(
    host, hostname, localhost, ssh_config, remote, singlenode, project_path, mock_hosts
):
    remote = '--remote {}'.format(hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = '' # TODO
    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'bootstrap-eos') if remote else DEFAULT_SCRIPT_PATH

    res = run_script(
        localhost if remote else host,
        "{} {} {} {}".format(
            ssh_config, with_sudo, remote, '--singlenode' if singlenode else ''
        ),
        script_path=script_path
    )
    assert res.rc == 0

    eosnode_1_line = "SALT-ARGS: eosnode-1 state.apply components.post_setup"
    eosnode_2_line = "SALT-ARGS: eosnode-2 state.apply components.post_setup"

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

    stdout_lines = res.stdout.split(os.linesep)
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
