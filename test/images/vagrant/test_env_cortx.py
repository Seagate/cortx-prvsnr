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
import yaml

import test.helper as h

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_level():
    return 'base'


@pytest.fixture(scope='module')
def vagrantfile_tmpl():
    return h.PROJECT_PATH / 'test/Vagrantfile.bvt.tmpl'


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-deploy-ready')
@pytest.mark.hosts(['srvnode1'])
def test_singlenode_deploy_ready_env(mhostsrvnode1, request):
    # light check
    assert mhostsrvnode1.host.file(str(h.PRVSNR_REPO_INSTALL_DIR)).exists

    res = mhostsrvnode1.run(
        'bash {} -p cluster'
        .format(h.PRVSNR_REPO_INSTALL_DIR / 'cli/src/configure')
    )
    assert res.rc == 0

    pillar_file_dict = yaml.safe_load(res.stdout)
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt']['interfaces'] == 'lo'  # noqa: E501
    assert pillar_file_dict['cluster']['srvnode-1']['network']['data']['public_interfaces'] == 'lo'  # noqa: E501
    def_gateway = mhostsrvnode1.check_output(
        'ip route | grep default | head -1'
    ).split()[2]
    assert def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt']['gateway'] == def_gateway  # noqa: E501
    assert pillar_file_dict['cluster']['srvnode-1']['hostname'] == mhostsrvnode1.hostname  # noqa: E501

    # FIXME path to cli scripts
    res = mhostsrvnode1.run(
        'bash {} -p release'
        .format(h.PRVSNR_REPO_INSTALL_DIR / 'cli/src/configure')
    )
    assert res.rc == 0

    pillar_file_dict = yaml.safe_load(res.stdout)
    assert (
        pillar_file_dict['release']['target_build'] ==
        request.config.getoption('cortx-release')
    )

    baseurl = mhostsrvnode1.check_output(
        'cat /etc/yum.repos.d/prvsnr.repo | grep baseurl'
    ).split('=')[1]
    assert baseurl == (
        'http://<cortx_release_server>/releases/cortx/{}'
        .format(request.config.getoption('prvsnr_release'))
    )

    mhostsrvnode1.check_output(
        'bash /opt/seagate/cortx/provisioner/cli/src/deploy -vv -S'
    )


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-cortx-deployed')
@pytest.mark.hosts(['srvnode1'])
def test_singlenode_cortx_deployed_env(mhostsrvnode1, request):
    # bootstrap the cluster
    h.bootstrap_cortx(mhostsrvnode1)

    # perform sanity checks
    # mhostsrvnode1.check_output(
    #     'bash -ex {}'
    #     .format(mhostsrvnode1.repo / 'sanity_tests/s3-sanity.sh')
    # )


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-cortx-ready')
@pytest.mark.hosts(['srvnode1'])
def test_singlenode_cortx_ready_env(mhostsrvnode1, request):
    mhostsrvnode1.check_output(
        'bash -ex /opt/seagate/cortx/provisioner/sanity_tests/s3-sanity.sh'
    )


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-deploy-ready')
@pytest.mark.hosts(['srvnode1'])
def test_s3_sanity_singlenode_env(
    mhostsrvnode1, ssh_config, mlocalhost,
    request, tmpdir_function, run_script
):
    remote = '--remote {}'.format(mhostsrvnode1.hostname)
    ssh_config = '--ssh-config {}'.format(ssh_config)

    res = run_script(
        "{} {} -p cluster".format(
            ssh_config, remote
        ),
        mhost=mlocalhost,
        script_name='configure'
    )
    assert res.rc == 0

    pillar_file_dict = yaml.safe_load(res.stdout)

    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt']['interfaces'] == mhostsrvnode1.interface  # noqa: E501
    assert pillar_file_dict['cluster']['srvnode-1']['network']['data']['public_interfaces'] == mhostsrvnode1.interface  # noqa: E501
    def_gateway = mhostsrvnode1.check_output(
        'ip route | grep default | head -1'
    ).split()[2]
    assert def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt']['gateway'] == def_gateway  # noqa: E501
