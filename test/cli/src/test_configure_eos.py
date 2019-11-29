import os
import pytest
import json
import logging

from test.helper import PRVSNR_REPO_INSTALL_DIR

logger = logging.getLogger(__name__)

# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/configure-eos"


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


@pytest.fixture(scope='module')
def local_scripts_path(project_path):
    return [
        str(project_path / 'cli/src/configure-eos'),
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


@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_configure_eos_show(
    host, hostname, localhost, ssh_config, remote, project_path, install_provisioner
):
    # Note. not parametrized per component since the test copies
    #       test_functions.sh:test_functions_eos_pillar_show_skeleton a lot
    component = 'cluster'

    # TODO python3.6 ???
    pillar_content = host.check_output(
        'python3.6 {0}/configure-eos.py {1} --show-{1}-file-format'.format(
            PRVSNR_REPO_INSTALL_DIR / 'cli' / 'utils', component
        )
    )

    remote = '--remote {}'.format(hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = '' # TODO
    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'configure-eos') if remote else DEFAULT_SCRIPT_PATH

    res = run_script(
        localhost if remote else host,
        "{} {} {} --show-file-format {}".format(
            ssh_config, with_sudo, remote, component
        ),
        script_path=script_path
    )
    assert res.rc == 0
    assert res.stdout.strip() == pillar_content


@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_configure_eos_update(
    host, hostname, host_tmpdir,
    localhost, tmp_path,
    ssh_config, remote, project_path,
    install_provisioner
):
    # Note. not parametrized per component since the test copies
    #       test_functions.sh:test_functions_eos_pillar_update a lot
    component = 'cluster'

    # 1. prepare some valid pillar for the component
    res = run_script(
        host,
        "--show-file-format {}".format(component),
    )
    assert res.rc == 0
    new_pillar_content = res.stdout

    component_pillar = '{}.sls'.format(component)
    tmp_file = tmp_path / component_pillar

        # TODO
        # - might need to update configure-eos.py to dump with endline at end
    tmp_file.write_text(new_pillar_content.strip() + '\n')
    if not remote:
        host_tmp_file = host_tmpdir / component_pillar
        localhost.check_output(
            "scp -F {0} {1} {2}:{3}".format(
                ssh_config,
                tmp_file,
                hostname,
                host_tmp_file
            )
        )
        tmp_file = host_tmp_file

    # 2. remove original pillar to ensure that coming update is applied
        # TODO better to have modified pillar
    original_pillar = PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / component_pillar
    host.check_output('rm -f {}'.format(original_pillar))

    # 3. call the script
    remote = '--remote {}'.format(hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = '' # TODO
    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'configure-eos') if remote else DEFAULT_SCRIPT_PATH

    res = run_script(
        localhost if remote else host,
        "{} {} {} --file {} {}".format(
            ssh_config, with_sudo, remote, tmp_file, component
        ),
        script_path=script_path
    )

    # 4. verify
    assert res.rc == 0

    # TODO
    # - check md5sum is everywhere available
    # - might be better to use pyyaml and compare objects instead
    tmp_file_hash = (localhost if remote else host).check_output('md5sum {}'.format(tmp_file))
    pillar_file_hash = host.check_output('md5sum {}'.format(original_pillar))
    assert tmp_file_hash.split()[0] == pillar_file_hash.split()[0]
