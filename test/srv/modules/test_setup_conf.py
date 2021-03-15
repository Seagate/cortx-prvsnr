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

import logging
import pytest

from salt.client import Caller


logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

test_data = [
  (
    "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/setup.yaml",
    "test:post_install"
  ),
  (
    "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/setup.yaml",
    "test:config"
  ),
  (
    "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/setup.yaml",
    "test:init"
  ),
  (
    "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/setup.yaml",
    "test:test"
  )
]


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
@pytest.mark.parametrize("config_path,config_key", test_data)
def test_conf_cmd(config_path: str, config_key: str):
    salt_client_caller = Caller()
    salt_client_caller.cmd('saltutil.clear_cache')
    salt_client_caller.cmd('saltutil.sync_modules')
    salt_client_caller.cmd(
      f"setup_conf.conf_cmd conf_file = {config_path} "
      f"conf_key={config_key}"
    )
