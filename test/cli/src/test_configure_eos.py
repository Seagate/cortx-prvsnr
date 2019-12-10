import os
import pytest
import logging
import yaml

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
@pytest.mark.eos_spec({'host': {'minion_id': 'some-minion-id', 'is_primary': True}})
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


# TODO
#  - mostly repeats 'test_functions_eos_pillar_update_and_load_default'
@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.eos_spec({'host': {'minion_id': 'some-minion-id', 'is_primary': True}})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_configure_eos_update_and_load_default(
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

    pillar_new_key = 'test'

    new_pillar_content = res.stdout
    new_pillar_dict = yaml.safe_load(new_pillar_content.strip())
    new_pillar_dict.update({pillar_new_key: "temporary"})

    component_pillar = '{}.sls'.format(component)
    tmp_file = tmp_path / component_pillar
    tmp_file.write_text(
        yaml.dump(new_pillar_dict, default_flow_style=False, canonical=False)
    )
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

    # 2. call the script to update
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

    # 3. verify
    assert res.rc == 0

    tmp_file_content = (localhost if remote else host).check_output('cat {}'.format(tmp_file))
    current_pillar = PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / component_pillar
    pillar_file_content = host.check_output('cat {}'.format(current_pillar))

    tmp_file_dict = yaml.safe_load(tmp_file_content)
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    assert tmp_file_dict == pillar_file_dict

    # 4. call the script to reset to defaults
    res = run_script(
        localhost if remote else host,
        "--load-default {} {} {} {}".format(
            ssh_config, with_sudo, remote, component
        ),
        script_path=script_path
    )

    # 5. verify
    assert res.rc == 0

    pillar_file_content = host.check_output('cat {}'.format(current_pillar))
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    del new_pillar_dict[pillar_new_key]
    assert new_pillar_dict == pillar_file_dict
# TODO
# - add testes for load defaults functionality
