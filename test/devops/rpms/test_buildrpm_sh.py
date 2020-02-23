import pytest
import logging

import test.helper as h


RPM_CONTENT_PATHS = ['pillar', 'srv', 'api']
RPM_CLI_CONTENT_PATHS = [
    'cli/utils',
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

    excluded = ['-name "{}"'.format(e) for e in ['__pycache__', '*.pyc', '*.pyo']]
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
    #   check that api is installed into python env
    assert 'eos-prvsnr' in mhost.check_output('pip3 list')
    mhost.check_output("python3 -c 'import provisioner'")
    #   check that prvsnrusers groups is created
    assert PRVSNRUSERS_GROUP in mhost.check_output("cat /etc/group")


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
        "cd {} && find . -maxdepth 1 \\( {} \\) -prune -o -type f -printf '%p\n'"
        .format(
            h.PRVSNR_REPO_INSTALL_DIR / 'cli',
            ' -o '.join(['-name "__pycache__"'])
        )
    ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)
    assert not diff_expected
    assert not diff_installed
