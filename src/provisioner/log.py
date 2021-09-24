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

import os

from cortx.utils.log import Log
from cortx.provisioner import const


class CortxProvisionerLog(Log):
    """ Redirect log message to log file and console using cortx utils logger """

    default_log_path = '/var/log/cortx'
    app_name = 'provisioner'
    logger = None

    @staticmethod
    def initialize(service_name, log_path=None, level='INFO', console_output=False):
        """
        Initialize and use cortx-utils logger to log message in file and console.
        If console_output is True, log message will be displayed in console.
        """
        if not CortxProvisionerLog.logger:
            log_path = log_path if log_path else CortxProvisionerLog.default_log_path
            log_path = os.path.join(log_path, CortxProvisionerLog.app_name)

            if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                level = 'INFO'

            Log.init(service_name, log_path, level=level, console_output=console_output)
            CortxProvisionerLog.logger = Log.logger


    @staticmethod
    def reinitialize(service_name, log_path=None, level='INFO', console_output=False):
        """
        Reinitialize cortx-utils logger with given log path

        Add captured log message from temporary log file to log file in
        configured log path
        """
        if Log.logger:

            log_path = log_path if log_path else CortxProvisionerLog.default_log_path
            log_path = os.path.join(log_path, CortxProvisionerLog.app_name)

            if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                level = 'INFO'

            # Remove current logging handlers before truncating
            for handler in Log.logger.handlers[:]:
                Log.logger.removeHandler(handler)

            temp_log_file = '%s/%s/%s.log' % (
                const.TMP_LOG_PATH, CortxProvisionerLog.app_name, const.SERVICE_NAME)

            if os.path.exists(temp_log_file):
                with open(temp_log_file, 'r') as f:
                    lines = f.read()
                with open(temp_log_file, 'w') as f:
                    f.write("")
                # Append log message in configured log file
                if not os.path.exists(log_path):
                    os.makedirs(log_path)
                with open(os.path.join(log_path, '%s.log' % const.SERVICE_NAME),
                        'a+') as f:
                    f.writelines(lines)

        Log.init(const.SERVICE_NAME, log_path, level=level, console_output=console_output)
