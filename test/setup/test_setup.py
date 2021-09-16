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
import traceback
import sys
import unittest
from cortx.utils.cmd_framework import Cmd
from cortx.setup import cortx_setup

solution_conf_url = "yaml://" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "cluster.yaml"))
cortx_conf_url = "yaml:///tmp/test.conf"

class TestSetup(unittest.TestCase):
    """Test EventMessage send and receive functionality."""

    def test_config_apply(self):
        """ Test Config Apply """

        rc = 0
        try:
            argv = [ 'config', 'apply', '-f', solution_conf_url, '-o', cortx_conf_url ]
            cmd = Cmd.get_command(sys.modules['cortx.setup.cortx_setup'], 'test_setup', argv)
            self.assertEqual(cmd.process(), 0)

        except Exception as e:
            print('Exception: ', e)
            sys.stderr.write("%s\n" % traceback.format_exc())
            rc = 1
        self.assertEqual(rc, 0)

# TODO: Uncomment. Test fails due to a bug
#
#    def test_cluster_bootstrap(self):
#        """ Test Cluster Bootstrap """
#
#        rc = 0
#        try:
#            argv = [ 'cluster', 'bootstrap', '1', cortx_conf_url ]
#            cmd = Cmd.get_command(sys.modules['cortx.setup.cortx_setup'], 'test_setup', argv)
#            self.assertEqual(cmd.process(), 0)
#
#        except Exception as e:
#            print('Exception: ', e)
#            sys.stderr.write("%s\n" % traceback.format_exc())
#            rc = 1
#        self.assertEqual(rc, 0)

if __name__ == '__main__':
    unittest.main()
