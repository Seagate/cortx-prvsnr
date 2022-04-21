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

import sys
import os
import traceback
import unittest
import yaml
from cortx.provisioner.provisioner import CortxProvisioner
from cortx.utils.conf_store import MappedConf, Conf

solution_cluster_url = "yaml://" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "cluster.yaml"))
solution_conf_url = "yaml://" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "config.yaml"))
cortx_conf_url = "yaml:///tmp/test_conf_store.conf"

def delete_file(file):
    """Delete Temporary file."""
    try:
        if os.path.exists(file):
            os.remove(file)
    except OSError as e:
        print(e)

class TestProvisioner(unittest.TestCase):

    """Test cortx_setup config and cluster functionality."""

    def test_config_apply_bootstrap(self):
        """ Test Config Apply """

        rc = 0
        try:
            CortxProvisioner.config_apply(solution_cluster_url, cortx_conf_url)
            CortxProvisioner.config_apply(solution_conf_url, cortx_conf_url, force_override=True)
        except Exception as e:
            print('Exception: ', e)
            sys.stderr.write("%s\n" % traceback.format_exc())
            rc = 1

        self.assertEqual(rc, 0)

        rc = 0
        try:
            CortxProvisioner.cluster_bootstrap(cortx_conf_url)
            CortxProvisioner.cluster_upgrade(cortx_conf_url)
        except Exception as e:
            print('Exception: ', e)
            sys.stderr.write("%s\n" % traceback.format_exc())
            rc = 1

        self.assertEqual(rc, 0)

    def test_add_num_keys(self):
        """Test add_num_keys interface."""
        data = {
                'a' : ['1', '2', '3'],
                'b' : '4',
                'c' : [{'5' : ['6', '7']}, '8']
        }
        test_index = 'test_index'
        config_path = "/tmp/sample_config.yaml"
        with open(config_path, 'w+') as config:
            config.write(yaml.dump(data))
        config_url = f"yaml://{config_path}"
        cortx_conf = MappedConf(config_url)
        CortxProvisioner._add_num_keys(cortx_conf)
        Conf.load(test_index, config_url)
        self.assertEqual(3, Conf.get(test_index, 'num_a'))
        self.assertEqual(2, Conf.get(test_index, 'c[0]>num_5'))
        delete_file(config_path)

if __name__ == '__main__':
    unittest.main()
