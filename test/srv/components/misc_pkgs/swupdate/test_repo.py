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

from pathlib import Path
import os
import pytest
import yaml

import logging

import test.helper as h

logger = logging.getLogger(__name__)


# TODO
#  - might makes sense. to verify for cluster case as well
#  - split into more focused scenarios
#  - tests for states relations
@pytest.mark.isolated  # noqa: C901 TODO improve
@pytest.mark.env_provider('vbox')  # mount makes docker inappropriate
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
def test_swupdate_repo(
    mhostsrvnode1, cortx_hosts, configure_salt, accept_salt_keys
):
    repo_dir = '/tmp/repo'
    iso_path = '/tmp/repo.iso'

    minion_id = cortx_hosts['srvnode1']['minion_id']
    pillar_path = h.PRVSNR_REPO_INSTALL_DIR / 'pillar/components/release.sls'
    release_pillar_str = mhostsrvnode1.check_output(
        'cat {}'.format(pillar_path)
    )
    release_pillar = yaml.safe_load(release_pillar_str)
    update_spec = release_pillar['cortx_release']['update']

    mhostsrvnode1.check_output(
        "mkdir -p {repo_dir}"
        " && cp {rpm_path} {repo_dir}"
        " && yum install -y createrepo genisoimage"
        " && createrepo {repo_dir}"
        " && mkisofs -graft-points -r -l -iso-level 2 -J -o {iso_path} {repo_dir}"  # noqa: E501
        .format(
            repo_dir=repo_dir,
            rpm_path=mhostsrvnode1.rpm_prvsnr,
            iso_path=iso_path
        )
    )

    def update_pillar():
        mhostsrvnode1.check_output(
            "echo '{}' >{}"
            " && salt '{}' saltutil.refresh_pillar"
            .format(
                yaml.dump(
                    release_pillar, default_flow_style=False, canonical=False
                ),
                pillar_path,
                minion_id
            )
        )

    def check_mounted(mount_dir):
        # check mounted
        mhostsrvnode1.check_output(
            'ls {} | grep {}'.format(mount_dir, h.PRVSNR_PKG_NAME)
        )
        # check a record is added into the fstab
        mhostsrvnode1.check_output(
            'grep {} /etc/fstab'.format(mount_dir)
        )

    def check_unmounted(mount_dir):
        # check the record is removed from the fstab
        res = mhostsrvnode1.run(
            'grep {} /etc/fstab'.format(mount_dir)
        )
        assert res.rc == 1
        # check mount point dir doesn't exist
        res = mhostsrvnode1.run(
            'ls {}'.format(mount_dir)
        )
        assert res.rc == 2

    base_repo_name = 'cortx_update'
    for release, source, expected_rpm_name in [
        ('1.2.3', Path(repo_dir), h.PRVSNR_PKG_NAME),
        ('1.2.4', Path(iso_path), h.PRVSNR_PKG_NAME),
        (
            '1.2.5',
            'http://mirror.ghettoforge.org/distributions/gf/el/7/gf/x86_64/',
            'gf-release'
        )  # just for an example
    ]:
        expected_repo_name = '{}_{}'.format(base_repo_name, release)

        if str(source) is iso_path:
            mount_dir = Path(update_spec['base_dir']) / release
        else:
            mount_dir = None

        if mount_dir:
            # check initial state: no mount point directory exists
            res = mhostsrvnode1.run('ls {}'.format(mount_dir))
            assert res.rc == 2

        # INSTALL
        # set source for the release
        if isinstance(source, Path):
            _source = (
                h.PRVSNR_USER_FILEROOT_DIR /
                h.PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR / release
            )
            pillar_source = 'dir'

            if source.suffix == '.iso':
                _source = Path("{}.iso".format(_source))
                pillar_source = 'iso'

            mhostsrvnode1.check_output('mkdir -p {}'.format(_source.parent))
            mhostsrvnode1.check_output('ln -s {} {}'.format(source, _source))
            source = _source
        else:
            pillar_source = source

        # TODO check metadata was cleaned after installation
        update_spec['repos'][release] = pillar_source
        update_pillar()
        # apply states
        mhostsrvnode1.check_output(
            "salt '{0}' state.apply components.misc_pkgs.swupdate.repo"
            .format(minion_id)
        )
        if mount_dir:
            check_mounted(mount_dir)
        # check repo is enabled
        mhostsrvnode1.check_output(
            'yum repolist enabled | grep {}'.format(expected_repo_name)
        )
        # check only one update repo is enabled
        res = mhostsrvnode1.check_output(
            'yum repolist enabled | grep {}'.format(base_repo_name)
        )
        assert len(res.strip().split(os.linesep)) == 1
        # check rpm is available
        mhostsrvnode1.check_output(
            "yum list available | grep '^{}.*{}$'"
            .format(expected_rpm_name, expected_repo_name)
        )

        # REMOVE
        # unset source for the release
        update_spec['repos'][release] = None
        update_pillar()
        # apply states
        mhostsrvnode1.check_output(
            "salt '{0}' state.apply components.misc_pkgs.swupdate.repo"
            .format(minion_id)
        )
        # check repo is not listed anymore
        res = mhostsrvnode1.run(
            'yum repolist enabled | grep {}'.format(expected_repo_name)
        )
        assert res.rc == 1
        # check no any update repo is listed
        res = mhostsrvnode1.run(
            'yum repolist enabled | grep {}'.format(base_repo_name)
        )
        assert res.rc == 1

        if mount_dir:
            check_unmounted(mount_dir)

        if isinstance(source, Path):
            mhostsrvnode1.check_output('rm -rf {}'.format(source))

    # empty list of repos
    update_spec['repos'] = {}
    update_pillar()
    # apply states, should just does nothing
    mhostsrvnode1.check_output(
        "salt '{0}' state.apply components.misc_pkgs.swupdate.repo"
        .format(minion_id)
    )
