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
import re
import yaml
from copy import deepcopy

import test.helper as h

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_level():
    return 'singlenode-bvt-ready'


@pytest.fixture(scope='module')
def vagrantfile_tmpl():
    return h.PROJECT_PATH / 'test/Vagrantfile.bvt.tmpl'


@pytest.fixture(scope='module')
def hosts_spec(hosts_spec):
    res = deepcopy(hosts_spec)
    vbox_settings = res['srvnode1']['remote']['specific']['vbox']
    vbox_settings['memory'] = 8192
    vbox_settings['cpus'] = 4
    vbox_settings['mgmt_disk_size'] = 4096
    vbox_settings['data_disk_size'] = 20480
    return res


def ensure_hw_configuration(mhost, tmpdir):
    logger.info("Ensuring HW configuration...")
    lsblk_res = mhost.check_output(
        "lsblk -l -d -S -p -n -b --output NAME,SIZE,TRAN | grep 'sas'"
    )
    logger.debug('SAS Block devices: {}'.format(lsblk_res))

    lsblk_res = lsblk_res.split('\n')
    assert len(lsblk_res) == 2

    dev1 = lsblk_res[0].split()
    dev2 = lsblk_res[1].split()
    if int(dev1[1]) < int(dev2[1]):
        mgmt_dev = dev1[0]
        data_dev = dev2[0]
    else:
        mgmt_dev = dev2[0]
        data_dev = dev1[0]

    # get current pillar data
    res = mhost.check_output(
        "bash {} --show-file-format cluster"
        .format(h.PRVSNR_REPO_INSTALL_DIR / 'cli/configure')
    )
    cluster_sls = yaml.safe_load(res)

    cluster_dev_data = cluster_sls['cluster']['srvnode-1']['storage']

    if (
        mgmt_dev != cluster_dev_data['metadata_devices'][0]
        or data_dev != cluster_dev_data['data_devices'][0]
    ):
        logger.warning(
            "Unexpected devices mapping: system - mgmt '{}', "
            "data '{}', cluster - {}."
            " Reconfiguring cluster.sls ..."
            .format(mgmt_dev, data_dev, cluster_dev_data)
        )
        cluster_dev_data['metadata_devices'][0] = mgmt_dev
        cluster_dev_data['data_devices'][0] = data_dev

        tmp_file = tmpdir / 'cluster.sls.new'
        tmp_file.write_text(
            yaml.dump(cluster_sls, default_flow_style=False, canonical=False)
        )

        remote_tmp_file = mhost.copy_to_host(tmp_file)
        mhost.check_output(
            "bash {} --file {} cluster"
            .format(
                h.PRVSNR_REPO_INSTALL_DIR / 'cli/configure',
                remote_tmp_file
            )
        )


def prepare_bvt_python_env(mhost, remote_bvt_repo_path):
    logger.info("Preparing python env")
    # TODO virtual python env
    mhost.check_output(
        'pip3 install --user -r {}'
        .format(remote_bvt_repo_path / 'requirements.txt')
    )


def configure_bvt_s3_env(mhost, remote_bvt_repo_path):
    logger.info("Configuring S3 environment")
    # setup aws account
    account_data = mhost.check_output(
        "s3iamcli CreateAccount -n root -e root@seagate.com"
        " --ldapuser sgiamadmin --ldappasswd ldapadmin"
    )
    m = re.match(
        r'.* AccessKeyId = ([^,]+), SecretKey = ([^, ]+)',
        account_data
    )
    aws_access_key = m.group(1)
    aws_secret_key = m.group(2)

    mhost.check_output(
        "s3iamcli createaccountloginprofile -n root --password seagate"
        " --access_key {} --secret_key {}"
        .format(aws_access_key, aws_secret_key)
    )
    mhost.check_output(
        "echo -e '[default]\naws_access_key_id={}\naws_secret_access_key={}\n'"
        " > ~/.aws/credentials"
        .format(aws_access_key, aws_secret_key)
    )

    # configure tests
    test_vars = {
        's3_server_ip': '127.0.0.1',
        's3_server_user': 'root',
        's3_server_pwd': 'seagate',
    }

    mhost.check_output(
        'echo {} | passwd --stdin {}'
        .format(test_vars['s3_server_pwd'], test_vars['s3_server_user'])
    )

    for name, value in test_vars.items():
        mhost.check_output(
            'sed -i "s~{name} = .*~{name} = \\"{value}\\"~g" "{fpath}"'
            .format(
                name=name,
                value=value,
                fpath=remote_bvt_repo_path / 'Libraries/global_vars.py'
            )
        )


def get_bvt_results(
    mhost,
    mlocalhost,
    local_path,
    success,
    remote_job_results_dir=Path('~/avocado/job-results/latest')
):
    logger.info("Processing results")
    remote_path = mhost.tmpdir / local_path.name

    logger.info("Dumping journal logs")
    mhost.check_output(
        "journalctl > {}"
        .format(remote_job_results_dir / 'journalctl.out.txt')
    )

    mhost.check_output(
        "tar czf {} -C {} .".format(remote_path, remote_job_results_dir)
    )

    _local_path = mhost.copy_from_host(remote_path)
    mlocalhost.check_output('cp -fv {} {}'.format(_local_path, local_path))
    logger.info("Stored results as '{}'".format(local_path))


@pytest.mark.timeout(3600)
@pytest.mark.cortx_bvt
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')
@pytest.mark.env_level('singlenode-bvt-ready')
@pytest.mark.hosts(['srvnode1'])
def test_bvt(mlocalhost, mhostsrvnode1, request, tmpdir_function):
    cortx_release = mhostsrvnode1.check_output(
        "grep target_build '{}'"
        .format(h.PRVSNR_REPO_INSTALL_DIR / 'pillar/components/release.sls')
    ).split()[1]
    assert cortx_release == request.config.getoption("cortx_release")
    logger.info("Target release is set to '{}'".format(cortx_release))

    local_bvt_repo_path = Path(request.config.getoption("bvt_repo_path"))
    bvt_test_targets = Path(request.config.getoption("bvt_test_targets"))
    local_bvt_results = Path(request.config.getoption("bvt_results_path"))

    assert local_bvt_repo_path.exists()

    # upload tests to the remote
    remote_bvt_repo_archive_path = mhostsrvnode1.copy_to_host(
        local_bvt_repo_path
    )
    remote_bvt_repo_path = remote_bvt_repo_archive_path.parent / 'cortx-test'
    mhostsrvnode1.check_output(
        'mkdir -p "{0}"; tar -zxf "{1}" -C "{0}" --strip-components=1'
        .format(remote_bvt_repo_path, remote_bvt_repo_archive_path),
        force_dump=True
    )

    ensure_hw_configuration(mhostsrvnode1, tmpdir_function)

    prepare_bvt_python_env(mhostsrvnode1, remote_bvt_repo_path)

    h.bootstrap_cortx(mhostsrvnode1)

    configure_bvt_s3_env(mhostsrvnode1, remote_bvt_repo_path)

    # list tests
    logger.info("Discovering tests")
    res = mhostsrvnode1.check_output(
        'cd {} && python3 -m avocado list {}'
        .format(remote_bvt_repo_path, bvt_test_targets)
    )
    logger.info('Discovered tests: {}'.format(res))

    # run tests
    logger.info("Running tests")
    import subprocess
    res = subprocess.run(
        (
            "ssh -F {} {} 'cd {} && python3 -m avocado run {}'"
            .format(
                mhostsrvnode1.ssh_config,
                mhostsrvnode1.hostname,
                remote_bvt_repo_path,
                bvt_test_targets
            )
        ),
        shell=True,
        check=False,
        universal_newlines=True
    )

    get_bvt_results(
        mhostsrvnode1,
        mlocalhost,
        local_bvt_results,
        success=(res.returncode == 0)
    )

    assert res.returncode == 0
