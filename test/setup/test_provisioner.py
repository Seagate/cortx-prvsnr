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
from cortx.provisioner.provisioner import CortxProvisioner

solution_cluster_url = "yaml://" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "cluster.yaml"))
solution_conf_url = "yaml://" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "config.yaml"))
cortx_conf_url = "yaml:///tmp/test_conf_store.conf"


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


if __name__ == '__main__':
    unittest.main()
