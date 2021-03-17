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
import logging
from pathlib import Path

from test.helper import install_provisioner_api
from provisioner.config import PRVSNR_ROOT_DIR, PRVSNR_PILLAR_DIR
from provisioner.utils import dump_yaml

logger = logging.getLogger(__name__)


@pytest.fixture(params=["py", "cli", "pycli"])
def api_type(request):
    return request.param


@pytest.fixture(params=["sync", "salt_sync", "salt_async"])
def api_run_mode(request):
    return request.param


@pytest.fixture
def test_pillar_sls(tmpdir_function, cortx_hosts, project_path):

    def _f(mhost):
        test_pillar = {
            'test': {
                'simple': 1,
                'dict': {
                    "2": {
                        "3": 4
                    }
                },
                'list': [5, 6, 7]
            }
        }

        tmp_file = tmpdir_function / 'test.sls'
        dump_yaml(tmp_file, test_pillar)

        # Note. cluster.sls is used as one of listed in pillar/top.sls
        mhost.copy_to_host(
            tmp_file,
            host_path=Path(
                "{}/components/cluster.sls"
                .format(PRVSNR_PILLAR_DIR)
            )
        )

        mhost.check_output(
            "salt '{}' saltutil.refresh_pillar"
            .format(cortx_hosts['srvnode1']['minion_id'])
        )

    return _f


@pytest.fixture
def run_test(
    request, api_type, api_run_mode, run_test, cortx_hosts, project_path
):
    def f(mhost, *args, env=None, **kwargs):
        if env is None:
            env = {}

        minion_id = cortx_hosts['srvnode1']['minion_id']

        env['TEST_API_TYPE'] = api_type
        env['TEST_MINION_ID'] = minion_id

        if api_run_mode == 'salt_async':
            env['TEST_RUN_ASYNC'] = 'yes'

        if api_run_mode == 'sync':
            env['PRVSNR_SALT_JOB'] = 'no'
        else:
            env['PRVSNR_SALT_JOB'] = 'yes'
            mhost.copy_to_host(
                project_path / 'srv/_modules/prvsnr.py',
                PRVSNR_ROOT_DIR / 'srv/_modules/prvsnr.py'
            )
            mhost.check_output(
                "salt-run saltutil.sync_modules"
            )
            mhost.check_output(
                "salt '{}' saltutil.sync_modules".format(minion_id)
            )

        return run_test(mhost, *args, env=env, **kwargs)

    return f


# TODO split to different tests per each test case
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_external_auth(
    mhostsrvnode1, run_test
):
    username = 'someuser'
    password = '123456'
    group = 'prvsnrusers'  # check for user from default group `prvsnrusers`

    # CASE 1. do not create user at first
    run_test(
        mhostsrvnode1, username=username, password=password,
        expected_exc='AuthenticationError'
    )

    # CASE 2. create user but do not add to group for now
    mhostsrvnode1.check_output(
        "adduser {0} && echo {1} | passwd --stdin {0}"
        .format(username, password)
    )

    # Note. changing current user actually might be not needed
    # but it's better to cover that case as well
    run_test(
        mhostsrvnode1, username=username, password=password,
        expected_exc='AuthorizationError'
    )
    run_test(
        mhostsrvnode1, curr_user=username, username=username,
        password=password,
        expected_exc='AuthorizationError'
    )

    # CASE 3. add to group now
    mhostsrvnode1.check_output(
        "groupadd {0} && usermod -a -G {0} {1}"
        .format(group, username)
    )
    run_test(mhostsrvnode1, username=username, password=password)
    run_test(
        mhostsrvnode1, curr_user=username, username=username, password=password
    )


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_pillar_get_set(
    mhostsrvnode1, run_test, test_pillar_sls
):
    test_pillar_sls(mhostsrvnode1)
    run_test(mhostsrvnode1)


# TODO
#   - timeout is high because of vbox env build,
#     need to dseparate build logic fromAexplore ways how
#     to separate that (less timeout if env is ready)
# Note. ntpd service doesn't work in docker without additional tricks
# (if it's actually possible)
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_set_ntp(
    mhostsrvnode1, run_test
):
    mhostsrvnode1.check_output("yum install -y ntp")
    run_test(mhostsrvnode1)
    # TODO
    #   - run ntp.config state and check that nothing changed


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_set_network(
    mhostsrvnode1, run_test, cortx_hosts, project_path
):
    mhostsrvnode1.copy_to_host(
        project_path / "pillar/samples/dualnode.cluster.sls",
        host_path=Path(
            "{}/pillar/components/cluster.sls"
            .format(PRVSNR_ROOT_DIR)
        )
    )

    mhostsrvnode1.check_output(
        "salt '{}' saltutil.refresh_pillar"
        .format(cortx_hosts['srvnode1']['minion_id'])
    )

    run_test(mhostsrvnode1)


# TODO DOC example how to parametrize cluster/singlenode
# TODO DOC dynamic markers, dynamic fixtures
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.parametrize(
    "cluster", [True, False], ids=['cluster', 'singlenode']
)
def test_set_swupdate_repo(
    request, cluster, api_type, api_run_mode
):
    if cluster:
        request.applymarker(pytest.mark.env_level('salt-installed'))
        request.applymarker(pytest.mark.hosts(['srvnode1', 'srvnode2']))
        request.getfixturevalue('configure_salt')
        request.getfixturevalue('accept_salt_keys')
    else:
        request.applymarker(pytest.mark.hosts(['srvnode1']))

    mhostsrvnode1 = request.getfixturevalue('mhostsrvnode1')
    run_test = request.getfixturevalue('run_test')

    repo_dir = Path('/tmp/repo')
    iso_path = Path('/tmp/repo.iso')

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
    run_test(mhostsrvnode1, env={
        'TEST_MODE': 'cluster' if cluster else 'singlenode',
        'TEST_REPO_DIR': repo_dir,
        'TEST_REPO_ISO_PATH': iso_path,
    })


@pytest.mark.skip(reason="WIP")
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_set_swupdate_repo_for_reinstall(
    mhostsrvnode1, mlocalhost, run_test, rpm_build, request
):
    repo_dir = '/tmp/repo'

    mhostsrvnode1.check_output(
        "yum install -y {}".format(mhostsrvnode1.rpm_prvsnr)
    )

    test_file_path = 'srv/components/test.sls'

    def mhost_init_cb(mhost):
        mhost.check_output(
            'touch {}'.format(mhost.repo / test_file_path)
        )

    new_rpm = rpm_build(
        request,
        mlocalhost.tmpdir,
        rpm_type='core',
        mhost_init_cb=mhost_init_cb
    )
    new_rpm_remote = mhostsrvnode1.copy_to_host(new_rpm)

    mhostsrvnode1.check_output(
        "mkdir -p {repo_dir}"
        " && cp {rpm_path} {repo_dir}"
        " && yum install -y createrepo"
        " && createrepo {repo_dir}"
        .format(
            repo_dir=repo_dir,
            rpm_path=new_rpm_remote
        )
    )
    run_test(mhostsrvnode1, env={
        'TEST_REPO_DIR': repo_dir,
        'TEST_FILE_PATH': test_file_path
    })


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_cortx_update(
    mhostsrvnode1, run_test
):
    run_test(mhostsrvnode1)


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_pyinstaller_approach(
    mhostsrvnode1, tmpdir_function, request
):
    # Note. python system libarary dir
    # python3 -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'  # noqa: E501

    import inspect

    app_script = (
        """
            import importlib

            import provisioner
            import provisioner.freeze

            pillar = provisioner.pillar_get()
            print(pillar)

            try:
                importlib.import_module('salt')
            except ImportError:
                pass
            else:
                assert False, "salt is available"

            try:
                importlib.import_module('provisioner._api')
            except ImportError:
                pass
            else:
                assert False, "provisioner._api is available"
        """
    )
    app_script = inspect.cleandoc(app_script)

    app_path_local = tmpdir_function / 'myapp.py'
    app_path_local.write_text(app_script)
    app_path_remote = mhostsrvnode1.copy_to_host(app_path_local)

    install_provisioner_api(mhostsrvnode1)
    mhostsrvnode1.check_output("pip3 install pyinstaller")

    mhostsrvnode1.check_output(
        "cd {} && pyinstaller {}"
        .format(app_path_remote.parent, app_path_remote.name)
    )

    mhostsrvnode1.check_output(
        "{0}/dist/{1}/{1}"
        .format(app_path_remote.parent, app_path_remote.stem)
    )
