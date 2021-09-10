#!/bin/env python3 

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import traceback
import errno
import argparse
import inspect

from provisioner import CortxProvisioner
from cortx.utils.cmd_framework import Cmd

class CortxSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    @property
    def rc(self):
        return self._rc

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s" %(self._rc, self._desc)


class ConfigCmd(Cmd):
  """ PostInstall Setup Cmd """  

  name = "config"

  def __init__(self, args: dict):
    super().__init__(args)

  @staticmethod
  def add_args(parser: str):
    """ Add Command args for parsing """

    parser.add_argument('action', help='apply')
    parser.add_argument('solution_conf', help='Solution Config URL')
    parser.add_argument('cortx_conf', nargs='?', help='CORTX Config URL')

  def process(self):
    """ Apply Config """
    if self._args.action == 'apply':
      CortxProvisioner.config_apply(self._args.solution_conf, self._args.cortx_conf)


class ClusterCmd(Cmd):
  """ PostInstall Setup Cmd """

  name = "cluster"

  def __init__(self, args: dict):
    super().__init__(args)
     
  @staticmethod
  def add_args(parser: str):
    """ Add Command args for parsing """

    parser.add_argument('action', help='bootstrap')
    parser.add_argument('cortx_conf', nargs='?', help='CORTX Config URL')

  def process(self, *args, **kwargs):
    """ Bootsrap Cluster """
    if self._args.action == "bootstrap":
      CortxProvisioner.cluster_bootstrap(self._args.cortx_conf)


def main():
  try:
    # Parse and Process Arguments
    command = Cmd.get_command(sys.modules[__name__], 'cortx_setup', sys.argv[1:])
    rc = command.process() 

  except CortxSetupError as e:
    sys.stderr.write("%s\n\n" % str(e))
    sys.stderr.write("%s\n" % traceback.format_exc())
    rc = e.rc

  except Exception as e:
    sys.stderr.write("%s\n\n" % str(e))
    sys.stderr.write("%s\n" % traceback.format_exc())
    rc = errno.EINVAL

  return rc


if __name__ == "__main__":
  sys.exit(main())
