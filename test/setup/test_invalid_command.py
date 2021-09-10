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
import unittest
from cortx.utils.cmd_framework import Cmd


class TestCmd(Cmd):
  """ Test Command """

  def __init__(self, args: dict):
    super().__init__(args)

  def add_args(parser: str):
    parser.add_argument('param1', help='test')

  def process(self):
    return 0


class TestCmdFramework(unittest.TestCase):
    """Test EventMessage send and receive functionality."""

    def test_cmd_args(self):
        """ Test Cmd and Args """

        rc = 1
        try:
            argv = [ 'test', 'param1' ]
            cmd = Cmd.get_command(sys.modules[__name__], 'test', argv)

        except:
            rc = 0
        
        self.assertEqual(rc, 0)
            
         
if __name__ == '__main__':
    unittest.main()
