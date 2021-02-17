#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import pytest
import yaml
import string
import random
from pathlib import Path

import test.helper as h
import provisioner
from provisioner import config
from provisioner.utils import dump_yaml

from test.helper import (
    PRVSNRUSERS_GROUP, PROJECT_PATH
)

RPM_CONTENT_PATHS = ['pillar', 'srv']
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


def check_provisioner_group_dir(path, mhost):
    #   check that user dir is created
    #   and has proper access rights (ACL)
    assert mhost.host.file(str(path)).exists
    assert mhost.host.file(str(path)).is_directory
    assert mhost.host.file(str(path)).group == PRVSNRUSERS_GROUP

    mhost.check_output(
        "mkdir -p {}".format(path / 'aaa' / 'bbb')
    )
    mhost.check_output(
        "touch {}".format(path / 'aaa' / 'bbb' / 'ccc.sls')
    )
    expected_dir_perms = "drwxrwsr-x+ root prvsnrusers"
    dir_perms = mhost.check_output(
        "find {} -type d -exec ls -lad {{}} \\;  | "
        "awk '{{print $1 FS $3 FS $4}}' | sort -u"
        .format(path)
    )
    assert dir_perms == expected_dir_perms
    expected_file_perms = "-rw-rw-r--+ root prvsnrusers"
    file_perms = mhost.check_output(
        "find {} -type f -exec ls -la {{}} \\;  | "
        "awk '{{print $1 FS $3 FS $4}}' | sort -u"
        .format(path)
    )
    assert file_perms == expected_file_perms

    # check that user not from the provisioner group can't write there
    testuser = (
        ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    )
    mhost.check_output(
        "adduser {0} && echo {1} | passwd --stdin {0}"
        .format(testuser, 'somepass')
    )
    res = mhost.run(
        "su -l {} -c 'touch {}'".format(
            testuser,
            path / 'aaa' / 'bbb' / 'ccc2.sls'
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
            path / 'aaa' / 'bbb' / 'ccc2.sls'
        )
    )


def check_post_section(mhost, api_version=None):
    if api_version is None:
        api_version = provisioner.__version__

    pip_packages = mhost.host.pip_package.get_packages(pip_path='pip3')
    assert provisioner.__title__ in pip_packages
    assert pip_packages[provisioner.__title__][
        'version'
    ] == api_version

    #   check that prvsnrusers groups is created
    assert mhost.host.group(PRVSNRUSERS_GROUP).exists

    for path in (
        h.PRVSNR_USER_PILLAR_DIR,
        h.PRVSNR_USER_FILEROOT_DIR,
        h.PRVSNR_LOG_ROOT_DIR
    ):
        check_provisioner_group_dir(path, mhost)


def test_rpm_prvsnr_is_buildable(rpm_prvsnr):
    pass


@pytest.mark.skip('EOS-11650')
@pytest.mark.isolated
@pytest.mark.env_level('base')
def test_rpm_prvsnr_depends_on_salt_3001(mhost):
    depends = mhost.check_output('rpm -qpR {}'.format(mhost.rpm_prvsnr))
    assert 'salt-master = 3002\n' in depends
    assert 'salt-minion = 3002\n' in depends


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


@pytest.mark.isolated
@pytest.mark.verifies('EOS-6021')
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_reinstall_retains_configuration(
    mhost, mlocalhost, tmpdir_function
):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr))
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr_api))

    cluster_config_str = mhost.check_output(
        'provisioner configure_cortx cluster --show'
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
        'provisioner configure_cortx cluster --source {}'
        .format(tmp_file_remote)
    )

    mhost.check_output('yum reinstall -y {}'.format(mhost.rpm_prvsnr))
    cluster_config_str = mhost.check_output(
        'provisioner configure_cortx cluster --show'
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


def test_rpm_prvsnr_api_is_buildable(rpm_prvsnr_api):
    pass


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_api_installation(mhost, mlocalhost):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr_api))

    # check post install sections
    # TODO check salt config files replacement
    #   check that api is installed into python env and have proper version
    check_post_section(mhost)

    version = mhost.check_output('provisioner --version')
    assert version == provisioner.__version__


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_api_removal(mhost, mlocalhost):
    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr_api))
    mhost.check_output('yum remove -y python36-cortx-prvsnr')
    #   check that api is removed from python env
    pip_packages = mhost.host.pip_package.get_packages(pip_path='pip3')
    assert provisioner.__title__ not in pip_packages
    #   check that prvsnrusers group still exists
    assert mhost.host.group(PRVSNRUSERS_GROUP).exists


@pytest.mark.isolated
@pytest.mark.verifies('EOS-7327')
@pytest.mark.env_level('salt-installed')
def test_rpm_prvsnr_api_provioner_is_available_after_update(
    mhost, mlocalhost, tmpdir_function, rpm_build, request
):
    version = provisioner.__version__
    parts = version.split('.')
    parts[0] = str(int(parts[0]) + 1)
    new_version = '.'.join(parts)

    mhost.check_output('yum install -y {}'.format(mhost.rpm_prvsnr_api))

    def mhost_init_cb(mhost):
        mhost.check_output(
            "sed -i 's/__version__ = .*/__version__ = \"{}\"/g' {}"
            .format(
                new_version,
                mhost.repo / 'api/python/provisioner/__metadata__.py'
            )
        )

    new_rpm = rpm_build(
        request,
        tmpdir_function,
        mhost_init_cb=mhost_init_cb,
        rpm_type='api',
        pkg_version='2'  # just to check that param works as well
    )
    new_rpm_remote = mhost.copy_to_host(new_rpm)

    mhost.check_output('yum install -y {}'.format(new_rpm_remote))
    check_post_section(mhost, api_version=new_version)


@pytest.mark.env_level('base')
def test_build_bundles(mhost, tmpdir_function):
    res = []

    deploy_cortx_dir = tmpdir_function / 'cortx-deploy'
    deploy_bundle_dir = tmpdir_function / 'cortx-deploy-bundle'
    upgrade_bundle_dir = tmpdir_function / 'cortx-upgrade'

    build_script = (
        Path(mhost.repo)
        / 'srv/components/misc_pkgs/mocks/cortx/files/scripts/buildbundle.sh'
    )

    # XXX hard-coded
    for b_dir, b_type, b_version in [
        (deploy_cortx_dir, 'deploy-cortx', '2.0.0'),
        (deploy_bundle_dir, 'deploy-bundle', '2.0.0'),
        (upgrade_bundle_dir, 'upgrade', '2.1.0')
    ]:
        mhost.check_output(
            f"{build_script} -o {b_dir} -t {b_type} -r {b_version} --gen-iso"
        )
        res.append(mhost.copy_from_host(b_dir.with_suffix('.iso')))

    for iso_path in res:
        dest = PROJECT_PATH / f"tmp/{iso_path.name}"
        dest.write_bytes(iso_path.read_bytes())


@pytest.mark.env_level('base')
def test_build_isos(
    mhost, rpm_prvsnr, rpm_prvsnr_api, tmpdir_function
):
    res = []

    mhost.check_output("yum install -y createrepo genisoimage")
    single_repo = tmpdir_function / 'single'
    swupdate_repo = tmpdir_function / 'cortx'
    cortx_repo = single_repo / config.CORTX_ISO_DIR
    deps_repo = single_repo / config.CORTX_3RD_PARTY_ISO_DIR

    release_info = {
        'BUILD': '277',
        'DATETIME': '14-Oct-2020 11:21 UTC',
        'KERNEL': '3.10.0_1062.el7',
        'NAME': 'CORTX',
        'OS': 'Red Hat Enterprise Linux Server release 7.7 (Maipo)',
        'VERSION': '1.0.0',
        'COMPONENTS': [
            'cortx-csm_agent-1.0.0-25_9d988be.x86_64.rpm',
            'cortx-csm_web-1.0.0-58_65d6f8b.x86_64.rpm',
            'cortx-ha-1.0.0-34_eacae4e.x86_64.rpm',
            'cortx-hare-1.0.0-50_git584adaa.el7.x86_64.rpm',
            'cortx-libsspl_sec-1.0.0-33_gitf0c05e3.el7.x86_64.rpm',
            'cortx-libsspl_sec-devel-1.0.0-33_gitf0c05e3.el7.x86_64.rpm',
            'cortx-libsspl_sec-method_none-1.0.0-33_gitf0c05e3.el7.x86_64.rpm',
            'cortx-libsspl_sec-method_pki-1.0.0-33_gitf0c05e3.el7.x86_64.rpm',
            'cortx-motr-1.0.0-45_git7fc6c26_3.10.0_1062.el7.x86_64.rpm',
            'cortx-motr-devel-1.0.0-45_git7fc6c26_3.10.0_1062.el7.x86_64.rpm',
            'cortx-motr-tests-ut-1.0.0-45_git7fc6c26_3.10.0_1062.el7.x86_64.rpm',  # noqa: E501
            'cortx-prvsnr-1.0.0-75_gitb9b751c_el7.x86_64.rpm',
            'cortx-prvsnr-cli-1.0.0-75_gitb9b751c_el7.x86_64.rpm',
            'cortx-s3iamcli-1.0.0-75_git28a01f6.noarch.rpm',
            'cortx-s3iamcli-devel-1.0.0-75_git28a01f6.noarch.rpm',
            'cortx-s3server-1.0.0-75_git28a01f6_el7.x86_64.rpm',
            'cortx-sspl-1.0.0-33_gitf0c05e3.el7.noarch.rpm',
            'cortx-sspl-cli-1.0.0-33_gitf0c05e3.el7.noarch.rpm',
            'cortx-sspl-test-1.0.0-33_gitf0c05e3.el7.noarch.rpm',
            'python36-cortx-prvsnr-0.39.0-75_gitb9b751c.x86_64.rpm',
            'uds-pyi-1.1.1-1.r6.el7.x86_64.rpm',
            'udx-discovery-0.1.2-3.el7.x86_64.rpm'
        ]
    }

    for pkg, repo_dir in (
        ('prvsnr', cortx_repo),
        ('prvsnr_api', deps_repo)
    ):
        iso_path = repo_dir.with_suffix('.iso')

        mhost.check_output(
            "mkdir -p {repo_dir} {swupdate_repo}"
            " && cp {rpm_path} {repo_dir}"
            " && cp {rpm_path} {swupdate_repo}"
            " && createrepo {repo_dir}"
            " && mkisofs -graft-points -r -l -iso-level 2 -J -o {iso_path} {repo_dir}"  # noqa: E501
            .format(
                repo_dir=repo_dir,
                swupdate_repo=swupdate_repo,
                rpm_path=getattr(mhost, f"rpm_{pkg}"),
                iso_path=iso_path
            )
        )
        res.append(mhost.copy_from_host(iso_path))

    # prepare single iso
    iso_path = single_repo.with_suffix('.iso')
    mhost.check_output(
        "mkisofs -graft-points -r -l -iso-level 2 -J -o {iso_path} {repo_dir}"  # noqa: E501
        .format(
            repo_dir=single_repo,
            iso_path=iso_path
        )
    )
    res.append(mhost.copy_from_host(iso_path))

    # prepare swupdate iso
    iso_path = swupdate_repo.with_suffix('.iso')

    release_info_file = tmpdir_function / config.RELEASE_INFO_FILE
    dump_yaml(release_info_file, release_info)
    mhost.copy_to_host(
        release_info_file, swupdate_repo / release_info_file.name
    )

    mhost.check_output(
        (
            "createrepo {repo_dir}"
            " && mkisofs -graft-points -r -l -iso-level 2 -J -o {iso_path} {repo_dir}"  # noqa: E501
        ).format(
            repo_dir=swupdate_repo,
            iso_path=iso_path
        )
    )
    res.append(mhost.copy_from_host(iso_path))

    for iso_path in res:
        dest = PROJECT_PATH / f"tmp/{iso_path.name}"
        dest.write_bytes(iso_path.read_bytes())
