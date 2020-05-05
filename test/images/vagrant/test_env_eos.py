import pytest
import logging
import yaml

import test.helper as h

from test.cli.src.conftest import run_script

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
@pytest.mark.hosts(['eosnode1'])
def test_singlenode_deploy_ready_env(mhosteosnode1, request):
    # light check
    assert mhosteosnode1.host.file(str(h.PRVSNR_REPO_INSTALL_DIR)).exists

    res = mhosteosnode1.run(
        'bash {} -p cluster'.format(h.PRVSNR_REPO_INSTALL_DIR / 'cli/src/configure-eos')
    )
    assert res.rc == 0

    pillar_file_dict = yaml.safe_load(res.stdout)
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['iface'] == 'lo'
    assert pillar_file_dict['cluster']['srvnode-1']['network']['data_nw']['iface'] == 'lo'
    def_gateway = mhosteosnode1.check_output('ip route | grep default | head -1').split()[2]
    assert def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['gateway'] == def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['hostname'] == mhosteosnode1.hostname

    # FIXME path to cli scripts
    res = mhosteosnode1.run(
        'bash {} -p release'.format(h.PRVSNR_REPO_INSTALL_DIR / 'cli/src/configure-eos')
    )
    assert res.rc == 0

    pillar_file_dict = yaml.safe_load(res.stdout)
    assert pillar_file_dict['eos_release']['target_build'] == request.config.getoption('eos_release')

    baseurl = mhosteosnode1.check_output(
        'cat /etc/yum.repos.d/prvsnr.repo | grep baseurl'
    ).split('=')[1]
    assert baseurl == (
        'http://ci-storage.mero.colo.seagate.com/releases/eos/{}'
        .format(request.config.getoption('prvsnr_release'))
    )

    mhosteosnode1.check_output('bash /opt/seagate/eos-prvsnr/cli/src/deploy-eos -vv -S')


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-eos-deployed')
@pytest.mark.hosts(['eosnode1'])
def test_singlenode_eos_deployed_env(mhosteosnode1, request):
    # bootstrap the cluster
    h.bootstrap_eos(mhosteosnode1)

    # perform sanity checks
    # mhosteosnode1.check_output(
    #     'bash -ex {}'
    #     .format(mhosteosnode1.repo / 'sanity_tests/s3-sanity.sh')
    # )



@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-eos-ready')
@pytest.mark.hosts(['eosnode1'])
def test_singlenode_eos_ready_env(mhosteosnode1, request):
    mhosteosnode1.check_output('bash -ex /opt/seagate/eos-prvsnr/sanity_tests/s3-sanity.sh')


@pytest.mark.skip
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-deploy-ready')
@pytest.mark.hosts(['eosnode1'])
def test_s3_sanity_singlenode_env(
    mhosteosnode1, ssh_config, mlocalhost,
    request, tmpdir_function, run_script
):
    remote = '--remote {}'.format(mhosteosnode1.hostname)
    ssh_config = '--ssh-config {}'.format(ssh_config)

    res = run_script(
        "{} {} -p cluster".format(
            ssh_config, remote
        ),
        mhost=mlocalhost,
        script_name='configure-eos'
    )
    assert res.rc == 0

    pillar_file_dict = yaml.safe_load(res.stdout)

    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['iface'] == mhosteosnode1.iface
    assert pillar_file_dict['cluster']['srvnode-1']['network']['data_nw']['iface'] == mhosteosnode1.iface
    def_gateway = mhosteosnode1.check_output('ip route | grep default | head -1').split()[2]
    assert def_gateway
    assert pillar_file_dict['cluster']['srvnode-1']['network']['mgmt_nw']['gateway'] == def_gateway
