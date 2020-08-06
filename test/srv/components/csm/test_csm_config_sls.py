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
from pathlib import Path
from yaml import safe_dump

from test.helper import PRVSNRUSERS_GROUP

# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
@pytest.mark.env_level('salt-installed')
def test_setup_ssh_known_hosts(
    mhosteosnode1, eos_hosts, configure_salt, accept_salt_keys,
    sync_salt_modules, project_path, tmpdir_function
):
    minion_id = eos_hosts['eosnode1']['minion_id']

    # mock setup.yaml for csm
    csm_setup_yaml_mock_local = (
        tmpdir_function / 'setup.yaml'
    )

    csm_setup_yaml_mock_local.write_text(safe_dump({
        'csm': {
            'post_install': {
                'script': None
            }, 'config': {
                'script': None
            }
        }
    }))

    csm_setup_yaml_mock_remote = Path('/opt/seagate/eos/csm/conf/setup.yaml')

    mhosteosnode1.copy_to_host(
        csm_setup_yaml_mock_local,
        csm_setup_yaml_mock_remote
    )

    # user should exist
    mhosteosnode1.check_output('adduser csm')

    mhosteosnode1.check_output(
        "salt '{}' state.sls_id"
        " 'Add csm user to prvsnrusers group'"
        " components.csm.config"
        .format(minion_id)
    )

    assert mhosteosnode1.host.group(PRVSNRUSERS_GROUP).exists
    assert PRVSNRUSERS_GROUP in mhosteosnode1.host.user("csm").groups
