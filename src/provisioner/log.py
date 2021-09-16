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
    """ Cortx provisioner log """

    logger = None

    @staticmethod
    def init(service_name, log_path=None, console_output=False):
        """ Initialize log """

        if not log_path:
            log_path = os.path.join('/var/log/cortx', 'provisioner')

        log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', 'INFO')
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            log_level = 'INFO'

        Log.init(service_name, log_path, level=log_level,
                 console_output=console_output)
        CortxProvisionerLog.logger = Log.logger


if not CortxProvisionerLog.logger:
    CortxProvisionerLog.init("cortx_setup", console_output=True)
