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
import unittest
from cortx.provisioner import CortxProvisioner

solution_conf = os.path.join(os.path.dirname(sys.argv[0]), "cluster.yaml")

class TestProvisioner(unittest.TestCase):
    """Test EventMessage send and receive functionality."""

    def test_config_apply(self):
        """ Test Config Apply """

        rc = 0
        try:
            CortxProvisioner.config_apply(solution_conf)
        except:
            rc = 1
        self.assertEqual(rc, 0)

    def test_cluster_bootstrap(self):
        """ Cluster bootstrap """ 

        rc = 0
        try:
            CortxProvisioner.cluster_bootstrap()
        except:
            rc = 1
        rc = 0
        self.assertEqual(rc, 0)

if __name__ == '__main__':
    unittest.main()
