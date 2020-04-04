import pytest
import yaml

import test.helper as h
import provisioner


RPM_CONTENT_PATHS = ['pillar', 'srv', 'api']
RPM_CLI_CONTENT_PATHS = [
    'files/etc/salt',
    'files/etc/modprobe.d',
    'files/etc/yum.repos.d'
]
PRVSNRUSERS_GROUP = 'prvsnrusers'


def test_rpm_prvsnr_is_buildable(rpm_prvsnr):
    pass


@pytest.mark.isolated
@pytest.mark.env_level('base')
def test_rpm_prvsnr_depends_on_salt_2019_2_0(mhost):
    depends = mhost.check_output('rpm -qpR {}'.format(mhost.rpm_prvsnr))
    assert 'salt-master = 2019.2.0\n' in depends
    assert 'salt-minion = 2019.2.0\n' in depends


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_installation(mhost, mlocalhost):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))

    # check paths that were installed
    excluded = ['-name "{}"'.format(e) for e in h.REPO_BUILD_DIRS]
    expected = mlocalhost.check_output(
        "cd {} && find {} \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            mlocalhost.repo,
            ' '.join(RPM_CONTENT_PATHS),
            ' -o '.join(excluded)
        )
    ).split()

    excluded = [
        '-name "{}"'.format(e) for e in ['__pycache__', '*.pyc', '*.pyo']
    ]
    installed = mhost.check_output(
        "cd {} && find {} \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            h.PRVSNR_REPO_INSTALL_DIR,
            ' '.join(RPM_CONTENT_PATHS),
            ' -o '.join(excluded)
        )
    ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)
    assert not diff_expected
    assert not diff_installed

    # check post install sections
    # TODO check salt config files replacement
    #   check that api is installed into python env and have proper version
    assert 'eos-prvsnr' in mhost.check_output('pip3 list')
    assert provisioner.__version__ == mhost.check_output(
        "python3 -c 'import provisioner; print(provisioner.__version__)'"
    )

    #   check that prvsnrusers groups is created
    assert PRVSNRUSERS_GROUP in mhost.check_output("cat /etc/group")

    #   check that user pillar dir is created
    #   and has proper access rights (ACL)
    assert mhost.host.file(str(h.PRVSNR_USER_PILLAR_DIR)).exists
    assert mhost.host.file(str(h.PRVSNR_USER_PILLAR_DIR)).is_directory
    assert mhost.host.file(
        str(h.PRVSNR_USER_PILLAR_DIR)
    ).group == PRVSNRUSERS_GROUP

    mhost.check_output(
        "mkdir -p {}".format(h.PRVSNR_USER_PILLAR_DIR / 'aaa' / 'bbb')
    )
    mhost.check_output(
        "touch {}".format(h.PRVSNR_USER_PILLAR_DIR / 'aaa' / 'bbb' / 'ccc.sls')
    )
    expected_dir_perms = "drwxrwsr-x+ root prvsnrusers"
    dir_perms = mhost.check_output(
        "find {} -type d -exec ls -lad {{}} \\;  | "
        "awk '{{print $1 FS $3 FS $4}}' | sort -u"
        .format(h.PRVSNR_USER_PILLAR_DIR)
    )
    assert dir_perms == expected_dir_perms
    expected_file_perms = "-rw-rw-r--+ root prvsnrusers"
    file_perms = mhost.check_output(
        "find {} -type f -exec ls -la {{}} \\;  | "
        "awk '{{print $1 FS $3 FS $4}}' | sort -u"
        .format(h.PRVSNR_USER_PILLAR_DIR)
    )
    assert file_perms == expected_file_perms

    # check that user not from the provisioner group can't write there
    testuser = 'testuser'
    mhost.check_output(
        "adduser {0} && echo {1} | passwd --stdin {0}"
        .format(testuser, 'somepass')
    )
    res = mhost.run(
        "su -l {} -c 'touch {}'".format(
            testuser,
            h.PRVSNR_USER_PILLAR_DIR / 'aaa' / 'bbb' / 'ccc2.sls'
        )
    )
    assert res.rc != 0
    assert "Permission denied" in res.stderr

    # check that user from the provisioner group can write there
    mhost.check_output(
        "usermod -a -G {0} {1}"
        .format(PRVSNRUSERS_GROUP, testuser)
    )
    mhost.check_output(
        "su -l {} -c 'touch {}'".format(
            testuser,
            h.PRVSNR_USER_PILLAR_DIR / 'aaa' / 'bbb' / 'ccc2.sls'
        )
    )


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_removal(mhost, mlocalhost):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))
    mhost.check_output('yum remove -y eos-prvsnr')
    # TODO check salt config files restoration
    #   check that api is removed from python env
    assert 'eos-prvsnr' not in mhost.check_output('pip3 list')
    #   check that prvsnrusers groups is absent
    assert PRVSNRUSERS_GROUP not in mhost.check_output("cat /etc/group")


@pytest.mark.isolated
@pytest.mark.verifies('EOS-6021')
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_reinstall_retains_configuration(
    mhost, mlocalhost, tmpdir_function
):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))

    cluster_config_str = mhost.check_output(
        'provisioner configure_eos cluster --show'
    ).strip()
    cluster_config_dict = yaml.safe_load(cluster_config_str)

    new_dns_servers = ['1.2.3.4']
    cluster_config_dict['dns_servers'] = new_dns_servers

    tmp_file = tmpdir_function / 'cluster.sls'
    tmp_file.write_text(
        yaml.dump(
            cluster_config_dict, default_flow_style=False, canonical=False
        )
    )
    tmp_file_remote = mhost.copy_to_host(tmp_file)

    mhost.check_output(
        'provisioner configure_eos cluster --source {}'.format(tmp_file_remote)
    )

    mhost.check_output('yum reinstall -y {}'.format(mhost.rpm_prvsnr))
    cluster_config_str = mhost.check_output(
        'provisioner configure_eos cluster --show'
    ).strip()
    cluster_config_dict_new = yaml.safe_load(cluster_config_str)

    assert cluster_config_dict_new == cluster_config_dict


def test_rpm_prvsnr_cli_is_buildable(rpm_prvsnr_cli):
    pass


@pytest.mark.isolated
@pytest.mark.env_level('base')
def test_rpm_prvsnr_cli_installation(mhost, mlocalhost):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr_cli))

    excluded_dirs = ['-name "{}"'.format(d) for d in h.REPO_BUILD_DIRS]
    expected = mlocalhost.check_output(
        "cd {} && find {} \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            mlocalhost.repo,
            ' '.join(RPM_CLI_CONTENT_PATHS),
            ' -o '.join(excluded_dirs)
        )
    ).split()

    expected_ssh = mlocalhost.check_output(
        "cd {} && find .ssh \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            mlocalhost.repo / 'files',
            ' -o '.join(excluded_dirs)
        )
    ).split()

    installed = mhost.check_output(
        "cd {} && find {} \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            h.PRVSNR_REPO_INSTALL_DIR,
            ' '.join(RPM_CLI_CONTENT_PATHS),
            ' -o '.join(['-name "__pycache__"'])
        )
    ).split()

    installed_ssh = mhost.check_output(
        "cd /root && find .ssh \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            ' -o '.join(['-name "__pycache__"'])
        )
    ).split()

    try:
        del installed_ssh[installed_ssh.index('.ssh/authorized_keys_test')]
    except ValueError:
        pass

    expected += expected_ssh
    installed += installed_ssh

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)

    assert not diff_expected
    assert not diff_installed

    # TODO need to fix rpm structure for cli scripts
    expected = mlocalhost.check_output(
        "cd {} && find . \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            mlocalhost.repo / 'cli/src',
            ' -o '.join(excluded_dirs)
        )
    ).split()

    installed = mhost.check_output(
        "cd {} && find . -maxdepth 1 \\( {} \\) "
        "-prune -o -type f -printf '%p\n'"
        .format(
            h.PRVSNR_REPO_INSTALL_DIR / 'cli',
            ' -o '.join(['-name "__pycache__"'])
        )
    ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)
    assert not diff_expected
    assert not diff_installed
