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
import os
from urllib.parse import urlparse

from cortx.provisioner.provisioner import CortxProvisioner
from cortx.provisioner.error import CortxProvisionerError
from cortx.utils.cmd_framework import Cmd
from cortx.provisioner import PLog


class ConfigCmd(Cmd):
    """ Config Setup Cmd """

    name = 'config'

    def __init__(self, args: dict):
        """ Initialize Command line parameters """
        super().__init__(args)

    @staticmethod
    def add_args(parser: str):
        """ Add Command args for parsing """

        parser.add_argument('action', help='apply')
        parser.add_argument('-f', dest='solution_conf', \
            help='Solution Config URL')
        parser.add_argument('-o', dest='cortx_conf', nargs='?', \
            help='CORTX Config URL')

    def _validate(self):
        """ Validate config command args """

        if self._args.action not in ['apply']:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid action type')

        path = urlparse(self._args.solution_conf).path
        if not os.path.exists(path):
            raise CortxProvisionerError(errno.EINVAL,
                'Solution config URL %s does not exist' % self._args.solution_conf)

    def process(self):
        """ Apply Config """
        self._validate()

        if self._args.action == 'apply':
            CortxProvisioner.config_apply(self._args.solution_conf, self._args.cortx_conf)
        return 0


class ClusterCmd(Cmd):
    """ Cluster Setup Cmd """

    name = 'cluster'

    def __init__(self, args: dict):
        super().__init__(args)

    @staticmethod
    def add_args(parser: str):
        """ Add Command args for parsing """

        parser.add_argument('action', help='bootstrap')
        parser.add_argument('-f', dest='cortx_conf', help='Cortx Config URL')

    def _validate(self):
        """ Validate cluster command args """

        if self._args.action not in ['bootstrap']:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid action type')

        path = urlparse(self._args.cortx_conf).path
        if not os.path.exists(path):
            raise CortxProvisionerError(errno.EINVAL,
                'CORTX config URL %s does not exist' % self._args.cortx_conf)

    def process(self, *args, **kwargs):
        """ Bootsrap Cluster """
        self._validate()
        if self._args.action == 'bootstrap':
            CortxProvisioner.cluster_bootstrap(self._args.cortx_conf)
        return 0


def main():
    try:
        # Parse and Process Arguments
        command = Cmd.get_command(sys.modules[__name__], 'cortx_setup', \
            sys.argv[1:])
        rc = command.process()

    except CortxProvisionerError as e:
        PLog.error('%s' % str(e))
        PLog.error('%s' % traceback.format_exc())
        rc = e.rc

    except Exception as e:
        PLog.error('%s' % str(e))
        PLog.error('%s' % traceback.format_exc())
        rc = errno.EINVAL

    return rc


if __name__ == "__main__":
    sys.exit(main())
