import pytest
import yaml

import test.helper as h
import provisioner

from test.helper import PRVSNRUSERS_GROUP

RPM_CONTENT_PATHS = ['pillar', 'srv', 'api']
RPM_CLI_CONTENT_PATHS = [
    'cli/src',
    'files/.ssh',
    'files/etc/yum.repos.d'
]


def check_ssh_configuration(mhost, mlocalhost):
    # check .ssh dir
    assert mhost.host.file('/root/.ssh').exists
    assert mhost.check_output(
        "cd /root && find . -type d -name .ssh -perm 700 -printf '%p\n'"
    )

    # check .ssh files
    expected = mlocalhost.check_output(
        "cd {} && find .ssh -type f -printf '%p\n'"
        .format(mlocalhost.repo / 'files')
    ).split()

    installed = mhost.check_output(
        "cd /root && find .ssh -type f -perm 600 -printf '%p\n'"
    ).split()

    try:
        del installed[installed.index('.ssh/authorized_keys_test')]
    except ValueError:
        pass

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)

    assert not diff_expected
    assert not diff_installed


def check_provisioner_api_installation(mhost, api_version=None):
    if api_version is None:
        api_version = provisioner.__version__

    pip_packages = mhost.host.pip_package.get_packages(pip_path='pip3')
    assert provisioner.__title__ in pip_packages
    assert pip_packages[provisioner.__title__][
        'version'
    ] == api_version

    #   check that prvsnrusers groups is created
    assert mhost.host.group(PRVSNRUSERS_GROUP).exists

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

    # TODO IMPROVE
    #       - update logic (list of files to check)
    #       - resolve list of files/dirs dynamically

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
    check_provisioner_api_installation(mhost)


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_removal(mhost, mlocalhost):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))
    mhost.check_output('yum remove -y eos-prvsnr')
    # TODO check salt config files restoration
    #   check that api is removed from python env
    pip_packages = mhost.host.pip_package.get_packages(pip_path='pip3')
    assert provisioner.__title__ not in pip_packages
    #   check that prvsnrusers group still exists
    assert mhost.host.group(PRVSNRUSERS_GROUP).exists


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


@pytest.mark.isolated
@pytest.mark.verifies('EOS-7327')
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_provioner_is_available_after_update(
    mhost, mlocalhost, tmpdir_function, rpm_build, request
):
    version = provisioner.__version__
    parts = version.split('.')
    parts[0] = str(int(parts[0]) + 1)
    new_version = '.'.join(parts)

    def mhost_init_cb(mhost):
        mhost.check_output(
            "sed -i 's/__version__ = .*/__version__ = \"{}\"/g' {}"
            .format(
                new_version,
                mhost.repo / 'api/python/provisioner/__metadata__.py'
            )
        )

    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))

    new_rpm = rpm_build(
        request, tmpdir_function,
        mhost_init_cb=mhost_init_cb, cli=False, release_number=2
    )
    new_rpm_remote = mhost.copy_to_host(new_rpm)

    mhost.check_output('yum install -y {}'.format(new_rpm_remote))
    check_provisioner_api_installation(mhost, api_version=new_version)


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

    installed = mhost.check_output(
        "cd {} && find {} \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            h.PRVSNR_REPO_INSTALL_DIR,
            ' '.join(RPM_CLI_CONTENT_PATHS),
            ' -o '.join(['-name "__pycache__"'])
        )
    ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)

    assert not diff_expected
    assert not diff_installed

    # check post install section
    #   cli scripts are copied to production location
    expected = mlocalhost.check_output(
        "cd {} && find . \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            mlocalhost.repo / 'cli/src',
            ' -o '.join(excluded_dirs + ["-name '*.swp'"])
        )
    ).split()

    installed = mhost.check_output(
        "cd {} && find . \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            h.PRVSNR_REPO_INSTALL_DIR / 'cli',
            ' -o '.join(['-name "__pycache__"', '-name src'])
        )
    ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)
    assert not diff_expected
    assert not diff_installed

    #   ssh is configured
    check_ssh_configuration(mhost, mlocalhost)


@pytest.mark.isolated
@pytest.mark.verifies('EOS-7327')
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_installation_over_cli(mhost):
    cli_file = mhost.host.file(
        str(h.PRVSNR_ROOT_DIR / 'cli/setup-provisioner')
    )

    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr_cli))
    mtime1 = cli_file.mtime

    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))
    mtime2 = cli_file.mtime
    assert mtime2 > mtime1
