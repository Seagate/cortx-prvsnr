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

from cortx_provisioner import CortxProvisioner
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

    parser.add_argument('action', help='config action e.g. apply')
    parser.add_argument('args', nargs='+', help='config parameters')

  def process(self):
    """ Apply Config """
    if self._args.action == 'apply':
      num_args = len(self._args.args)
      if num_args < 0:
        raise CortxSetupError(errno.EINVAL, "Insufficient parameters for apply")
      solution_conf_url = self._args.args[0]
      cluster_conf_url = self._args.args[1]
      cortx_conf_url = self._args.args[2] if num_args > 2 else None
      CortxProvisioner.config_apply(solution_conf_url, cluster_conf_url,
        cortx_conf_url)


class ClusterCmd(Cmd):
  """ PostInstall Setup Cmd """

  name = "cluster"

  def __init__(self, args: dict):
    super().__init__(args)
     
  @staticmethod
  def add_args(parser: str):
    """ Add Command args for parsing """

    parser.add_argument('action', help='cluster bootstrap')
    parser.add_argument('args', nargs='*', default=[], help='args')

  def process(self, *args, **kwargs):
    """ Bootsrap Cluster """
    if self._args.action == "bootstrap":
      num_args = len(self._args.args)
      cortx_conf_url = self._args.args[0] if num_args > 0 else None
      CortxProvisioner.cluster_bootstrap(cortx_conf_url)


if __name__ == "__main__":
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

  sys.exit(rc)
