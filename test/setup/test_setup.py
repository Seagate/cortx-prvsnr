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
from cortx.setup import cortx_setup
from cortx.provisioner import const
from cortx.utils.cmd_framework import Cmd
from cortx.provisioner.log import CortxProvisionerLog, Log

solution_cluster_url = "yaml:///" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "cluster.yaml"))
solution_config_url = "yaml:///" + os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "config.yaml"))
cortx_conf_url = "yaml:///tmp/test.conf"

if Log.logger is None:
    CortxProvisionerLog.initialize(const.SERVICE_NAME, const.TMP_LOG_PATH)


class TestSetup(unittest.TestCase):

    """Test cortx_setup config and cluster functionality."""

    def test_001_config_apply(self):
        """ Test Config Apply """

        rc = 0
        try:
            for solution_conf_url in [solution_cluster_url, solution_config_url]:
                argv = ['config', 'apply', '-f', solution_conf_url, '-c', cortx_conf_url, '-o']
                cmd = Cmd.get_command(sys.modules['cortx.setup.cortx_setup'], 'test_setup', argv)
                self.assertEqual(cmd.process(), 0)

        except Exception as e:
            print('Exception: ', e)
            sys.stderr.write("%s\n" % traceback.format_exc())
            rc = 1
        self.assertEqual(rc, 0)

    def test_002_cluster_bootstrap(self):
        """ Test Cluster Bootstrap """

        rc = 0
        try:
            argv = ['cluster', 'bootstrap', '-c', cortx_conf_url]

            cmd = Cmd.get_command(sys.modules['cortx.setup.cortx_setup'], 'test_setup', argv)
            self.assertEqual(cmd.process(), 0)

        except Exception as e:
            print('Exception: ', e)
            sys.stderr.write("%s\n" % traceback.format_exc())
            rc = 1
        self.assertEqual(rc, 0)

    def test_cluster_upgrade(self):
        """Test Cluster Upgrade."""
        rc = 0
        try:
            argv = ['cluster', 'upgrade', '-c', cortx_conf_url]

            cmd = Cmd.get_command(sys.modules['cortx.setup.cortx_setup'], 'test_setup', argv)
            self.assertEqual(cmd.process(), 0)

        except Exception as e:
            print('Exception: ', e)
            sys.stderr.write("%s\n" % traceback.format_exc())
            rc = 1
        self.assertEqual(rc, 0)


if __name__ == '__main__':
    unittest.main()
