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


class TestInvalidClusterConf(unittest.TestCase):
    """ Test invalid cluster config """

    def test_invalid_cluster_config(self):
        """ Test config_apply for invalid cluster.yaml """

        cluster_conf_file_path = "/tmp/invalid_cluster.yaml"
        # cluster_id, node_types, nodes are missing in below data.
        # config_apply should fail.
        data = {
            "cluster": {
                "name": "cortx-cluster",
                "storage_sets": [
                    {"name": "storage-set-1"}
                ]
            }
        }
        f = open(cluster_conf_file_path, 'w+')
        f.write(yaml.dump(data))
        f.close()
        cluster_conf_url = f"yaml://{cluster_conf_file_path}"
        rc = 0
        try:
            CortxProvisioner.config_apply(cluster_conf_url, cortx_conf_url)

        except Exception as e:
            print(e)
            rc = 1

        self.assertEqual(rc, 1)
        os.remove(cluster_conf_file_path)

if __name__ == '__main__':
    unittest.main()
