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

from cortx.provisioner.provisioner import CortxProvisioner
from cortx.provisioner.error import CortxProvisionerError
from cortx.utils.cmd_framework import Cmd


class ConfigCmd(Cmd):
    """ Config Setup Cmd """

    name = "config"

    def __init__(self, args: dict):
        """ Initialize Command line parameters """
        super().__init__(args)

    @staticmethod
    def add_args(parser: str):
        """ Add Command args for parsing """

        parser.add_argument('action', help='apply')
        parser.add_argument('-f', dest='solution_conf', help='Solution Config URL')
        parser.add_argument('-o', dest='cortx_conf', nargs='?', help='CORTX Config URL')

    def process(self):
        """ Apply Config """
        if self._args.action == 'apply':
            CortxProvisioner.config_apply(self._args.solution_conf, self._args.cortx_conf)
        return 0


class ClusterCmd(Cmd):
    """ Cluster Setup Cmd """

    name = "cluster"

    def __init__(self, args: dict):
        super().__init__(args)

    @staticmethod
    def add_args(parser: str):
        """ Add Command args for parsing """

        parser.add_argument('action', help='bootstrap')
        parser.add_argument('node_id', help='node_id')
        parser.add_argument('cortx_conf', nargs='?', help='CORTX Config URL')

    def process(self, *args, **kwargs):
        """ Bootsrap Cluster """
        if self._args.action == "bootstrap":
            CortxProvisioner.cluster_bootstrap(self._args.node_id, self._args.cortx_conf)
        return 0


def main():
    try:
        # Parse and Process Arguments
        command = Cmd.get_command(sys.modules[__name__], 'cortx_setup', sys.argv[1:])
        rc = command.process()

    except CortxProvisionerError as e:
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
