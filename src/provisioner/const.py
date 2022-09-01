# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

from pathlib import Path

SERVICE_NAME = "cortx_setup"
APP_NAME = "provisioner"
ROOT_VAL= ["config", "cortx"]
TMP_LOG_PATH = "/tmp/%s" % APP_NAME
DEFAULT_LOG_PATH = "/var/log/cortx/%s" % APP_NAME
CONFIG_PATH="/etc/cortx/config"
MACHINE_ID_PATH = Path("/etc/cortx/config/machine-id")
DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
RELEASE_INFO_URL = "yaml:///opt/seagate/cortx/RELEASE.INFO"
# 'UPGRADE_MODE_KEY' constant for environmental variable of upgrade mode.
UPGRADE_MODE_KEY = "UPGRADE_MODE"
# 'UPGRADE_MODE_VAL' constant for default upgrade mode.
UPGRADE_MODE_VAL = ""
REQUIRED_EXTERNAL_SW = ['kafka', 'consul']
# Path to the location that holds the cortx gconf consul url.
CONSUL_CONF_URL = "/etc/cortx/consul_conf"
DEFAULT_CONSOLE_OUTPUT_LEVEL = "INFO"
