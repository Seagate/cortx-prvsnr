#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import os
import yaml
import unittest
from cortx.provisioner.provisioner import CortxProvisioner

cortx_conf_url = "yaml:///tmp/test_conf_store.conf"


class TestInvalidCortxConf(unittest.TestCase):
    """ Test invalid CORTX config """

    def test_invalid_cortx_config(self):
        """ Test config_apply for invalid config.yaml """

        config_conf_file_path = "/tmp/invalid_config.yaml"
        # 'common' are missing in below data.
        # config_apply should fail.
        data = {
            "cortx": {
                "external": ""
            }
        }
        f = open(config_conf_file_path, 'w+')
        f.write(yaml.dump(data))
        f.close()
        config_conf_url = f"yaml://{config_conf_file_path}"
        rc = 0
        try:
            CortxProvisioner.config_apply(config_conf_url, cortx_conf_url)

        except Exception as e:
            print(e)
            rc = 1

        self.assertEqual(rc, 1)
        os.remove(config_conf_file_path)

if __name__ == '__main__':
    unittest.main()
