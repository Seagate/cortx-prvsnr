#!/bin/env python3 

import sys
import traceback
import errno
import argparse
import inspect

from cortx_provisioner import CortxProvisioner


class CortxSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s" %(self._rc, self._desc)


class Cmd:
  """ Command """

  def __init__(self, args: dict):
    self._args = args

  @staticmethod
  def get_command(desc: str, argv: dict):
    """ Return the Command after parsing the command line. """

    parser = argparse.ArgumentParser(desc)
    subparsers = parser.add_subparsers()

    cmds = inspect.getmembers(sys.modules[__name__])
    cmds = [(x, y) for x, y in cmds if x.endswith("Cmd") and x != "Cmd"]
    for _, cmd in cmds:
      parser1 = subparsers.add_parser(cmd.name, help='%s %s' % (desc, cmd.name))
      parser1.set_defaults(command=cmd)
      cmd.add_args(parser1)

    args = parser.parse_args(argv)
    return args.command(args)


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
    command = Cmd.get_command('cortx_setup', sys.argv[1:])
    rc = command.process() 

  except Exception as e:
    sys.stderr.write("%s\n\n" % str(e))
    sys.stderr.write("%s\n" % traceback.format_exc())
    rc = errno.EINVAL

  sys.exit(rc)
