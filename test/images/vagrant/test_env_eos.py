#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['iface'] == 'lo'  # noqa: E501
    assert pillar_file_dict['cluster']['srvnode-1']['network']['data_nw']['iface'] == 'lo'  # noqa: E501
    def_gateway = mhostsrvnode1.check_output(
        'ip route | grep default | head -1'
    ).split()[2]
    assert def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['gateway'] == def_gateway  # noqa: E501
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
        'http://cortx-storage.colo.seagate.com/releases/cortx/{}'
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

    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['iface'] == mhostsrvnode1.iface  # noqa: E501
    assert pillar_file_dict['cluster']['srvnode-1']['network']['data_nw']['iface'] == mhostsrvnode1.iface  # noqa: E501
    def_gateway = mhostsrvnode1.check_output(
        'ip route | grep default | head -1'
    ).split()[2]
    assert def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['gateway'] == def_gateway  # noqa: E501
