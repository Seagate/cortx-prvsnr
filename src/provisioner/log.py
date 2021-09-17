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


class CortxProvisionerLog(Log):
    """ Redirect log message to log file and console using cortx utils logger """

    logger = None

    @staticmethod
    def init(service_name, log_path=None, level='INFO', console_output=False):
        """
        Initialize and use cortx-utils logger to log message in file and console.
        If console_output is True, log message will be displayed in console.
        """

        if not log_path:
            log_path = os.path.join('/var/log/cortx', 'provisioner')

        if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            level = 'INFO'

        Log.init(service_name, log_path, level=level, console_output=console_output)
        CortxProvisionerLog.logger = Log.logger


if not CortxProvisionerLog.logger:

    log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', 'INFO')
    CortxProvisionerLog.init("cortx_setup", level=log_level, console_output=True)
