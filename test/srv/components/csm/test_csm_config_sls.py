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
from pathlib import Path
from yaml import safe_dump

from test.helper import PRVSNRUSERS_GROUP


# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
def test_setup_ssh_known_hosts(
    mhostsrvnode1, cortx_hosts, configure_salt, accept_salt_keys,
    sync_salt_modules, project_path, tmpdir_function
):
    minion_id = cortx_hosts['srvnode1']['minion_id']

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

    # FIXME renaming
    csm_setup_yaml_mock_remote = Path('/opt/seagate/cortx/csm/conf/setup.yaml')

    mhostsrvnode1.copy_to_host(
        csm_setup_yaml_mock_local,
        csm_setup_yaml_mock_remote
    )

    # user should exist
    mhostsrvnode1.check_output('adduser csm')

    mhostsrvnode1.check_output(
        "salt '{}' state.sls_id"
        " 'Add csm user to prvsnrusers group'"
        " components.csm.config"
        .format(minion_id)
    )

    assert mhostsrvnode1.host.group(PRVSNRUSERS_GROUP).exists
    assert PRVSNRUSERS_GROUP in mhostsrvnode1.host.user("csm").groups
