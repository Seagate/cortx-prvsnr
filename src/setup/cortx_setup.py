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

from cortx.provisioner.log import CortxProvisionerLog, Log
from cortx.provisioner.provisioner import CortxProvisioner
from cortx.provisioner.error import CortxProvisionerError
from cortx.provisioner.validators import Validator
from cortx.utils.cmd_framework import Cmd
from cortx.provisioner import const


class ConfigCmd(Cmd):
    """ Config Setup Cmd """

    name = 'config'

    def __init__(self, args: dict):
        """ Initialize Command line parameters """
        super().__init__(args)

    @staticmethod
    def add_args(parser: str):
        """ Add Command args for parsing """

        parser.add_argument('action', help='apply, validate')
        parser.add_argument('-f', dest='solution_conf',
            help='Solution Config URL')
        parser.add_argument('-c', dest='cortx_conf', nargs='?',
            help='CORTX Config URL')
        parser.add_argument('-v', dest='validations', nargs='?',
            help='config validations')
        parser.add_argument('-o', dest='override', action='store_true',
            help='Force and override config')
        parser.add_argument('-l', dest='log_level', help='Log level')

    def _validate(self):
        """ Validate config command args """

        if self._args.action not in ['apply', 'validate']:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid action type')

        log_level = self._args.log_level
        if not log_level:
            log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', const.DEFAULT_LOG_LEVEL)
        if log_level not in const.SUPPORTED_LOG_LEVELS:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid log level')
        Log.logger.setLevel(log_level)

    def process(self):
        """ Apply Config """
        self._validate()
        if self._args.action == 'apply':
            force_override = True if self._args.override else False
            CortxProvisioner.config_apply(
                self._args.solution_conf, self._args.cortx_conf, force_override)
        if self._args.action == 'validate':
            validations = ['all']
            if self._args.validations is not None:
                validations = self._args.validations.split(',')
            Validator.validate(validations, self._args.solution_conf, self._args.cortx_conf)

        return 0


class ClusterCmd(Cmd):
    """ Cluster Setup Cmd """

    name = 'cluster'

    def __init__(self, args: dict):
        super().__init__(args)

    @staticmethod
    def add_args(parser: str):
        """ Add Command args for parsing """

        parser.add_argument('action', help='bootstrap, upgrade')
        parser.add_argument('-c', dest='cortx_conf', help='Cortx Config URL')
        parser.add_argument('-l', dest='log_level', help='Log level')
        parser.add_argument('-o', dest='override', action='store_true',
            help='Override deployment')

    def _validate(self):
        """ Validate cluster command args """

        if self._args.action not in ['bootstrap', 'upgrade']:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid action type')

        log_level = self._args.log_level
        if not log_level:
            log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', const.DEFAULT_LOG_LEVEL)
        if log_level not in const.SUPPORTED_LOG_LEVELS:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid log level')
        os.environ['CORTX_PROVISIONER_DEBUG_LEVEL'] = log_level

    def process(self, *args, **kwargs):
        """ Bootsrap Cluster """
        self._validate()
        force_override = True if self._args.override else False
        if self._args.action == 'bootstrap':
            CortxProvisioner.cluster_bootstrap(self._args.cortx_conf, force_override)
        if self._args.action == 'upgrade':
            CortxProvisioner.cluster_upgrade(self._args.cortx_conf, force_override)
        return 0


def main():
    CortxProvisionerLog.initialize(const.SERVICE_NAME, const.TMP_LOG_PATH)
    try:
        # Parse and Process Arguments
        command = Cmd.get_command(sys.modules[__name__], 'cortx_setup', \
            sys.argv[1:])
        rc = command.process()

    except CortxProvisionerError as e:
        Log.error('%s' % str(e))
        Log.error('%s' % traceback.format_exc())
        rc = e.rc

    except Exception as e:
        Log.error('%s' % str(e))
        Log.error('%s' % traceback.format_exc())
        rc = errno.EINVAL

    return rc


if __name__ == "__main__":
    sys.exit(main())
