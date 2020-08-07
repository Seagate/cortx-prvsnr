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

# TODO better correlation with post_env_run_hook routine
DEFAULT_SCRIPT_PATH = "/tmp/configure-eos"


@pytest.fixture(scope='module')
def env_level():
    return 'base'


@pytest.fixture(scope='module')
def script_name():
    return 'configure-eos'


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec(
    {'': {'minion_id': 'some-minion-id', 'is_primary': True}}
)
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_configure_cortx_show(
    mhost, mlocalhost, ssh_config, remote, install_provisioner, run_script
):
    # Note. not parametrized per component since the test copies
    #       test_functions.sh:test_functions_cortx_pillar_show_skeleton a lot
    component = 'cluster'

    h.install_provisioner_api(mhost)

    # TODO python3.6 ???
    pillar_content = mhost.check_output(
        'provisioner configure_eos {1} --show'.format(
            h.PRVSNR_REPO_INSTALL_DIR / 'cli' / 'utils', component
        )
    )

    remote = '--remote {}'.format(mhost.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = ''  # TODO

    res = run_script(
        "{} {} {} --show-file-format {}".format(
            ssh_config, with_sudo, remote, component
        ),
        mhost=(mlocalhost if remote else mhost)
    )
    assert res.rc == 0
    assert res.stdout.strip() == pillar_content


# TODO
#  - mostly repeats 'test_functions_cortx_pillar_update_and_load_default'
@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec(
    {'': {'minion_id': 'some-minion-id', 'is_primary': True}}
)
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_configure_cortx_update_and_load_default(
    mhost, mlocalhost, ssh_config, remote,
    install_provisioner, run_script
):
    # Note. not parametrized per component since the test copies
    #       test_functions.sh:test_functions_cortx_pillar_update_and_load_default
    #       a lot
    component = 'cluster'

    h.install_provisioner_api(mhost)

    # verify that the script accepts all pillar components
    for comp in h.PRVSNR_CORTX_COMPONENTS:
        run_script("--show-file-format {}".format(comp), mhost=mhost)

    # 1. prepare some valid pillar for the component
    res = run_script("--show-file-format {}".format(component), mhost=mhost)
    assert res.rc == 0

    pillar_new_key = 'test'

    new_pillar_content = res.stdout
    new_pillar_dict = yaml.safe_load(new_pillar_content.strip())
    new_pillar_dict.update({pillar_new_key: "temporary"})

    component_pillar = '{}.sls'.format(component)
    tmp_file = mlocalhost.tmpdir / component_pillar
    tmp_file.write_text(
        yaml.dump(new_pillar_dict, default_flow_style=False, canonical=False)
    )
    if not remote:
        host_tmp_file = mhost.tmpdir / component_pillar
        mlocalhost.check_output(
            "scp -F {0} {1} {2}:{3}".format(
                ssh_config,
                tmp_file,
                mhost.hostname,
                host_tmp_file
            )
        )
        tmp_file = host_tmp_file

    # 2. call the script to update
    remote = '--remote {}'.format(mhost.hostname) if remote else ''
    ssh_config = '--ssh-config {}'.format(ssh_config) if remote else ''
    with_sudo = ''  # TODO

    res = run_script(
        "{} {} {} --file {} {}".format(
            ssh_config, with_sudo, remote, tmp_file, component
        ),
        mhost=(mlocalhost if remote else mhost)
    )

    # 3. verify
    assert res.rc == 0

    tmp_file_content = (mlocalhost if remote else mhost).check_output(
        'cat {}'.format(tmp_file)
    )
    current_def_pillar = h.PRVSNR_PILLAR_DIR / 'components' / component_pillar
    current_user_pillar = h.PRVSNR_USER_PI_ALL_HOSTS_DIR / component_pillar
    pillar_file_content = mhost.check_output(
        'cat {}'.format(current_user_pillar)
    )

    tmp_file_dict = yaml.safe_load(tmp_file_content)
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    assert tmp_file_dict == pillar_file_dict

    # 4. call the script to reset to defaults
    res = run_script(
        "--load-default {} {} {} {}".format(
            ssh_config, with_sudo, remote, component
        ),
        mhost=(mlocalhost if remote else mhost)
    )

    # 5. verify
    assert res.rc == 0

    pillar_file_content = mhost.check_output(
        'cat {}'.format(current_def_pillar)
    )
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    del new_pillar_dict[pillar_new_key]
    assert new_pillar_dict == pillar_file_dict
# TODO
# - add testes for load defaults functionality
