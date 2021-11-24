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

SERVICE_NAME = "cortx_setup"
APP_NAME = "provisioner"
TMP_LOG_PATH = "/tmp/%s" % APP_NAME
DEFAULT_LOG_PATH = "/var/log/cortx/%s" % APP_NAME
DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
RELEASE_INFO_PATH = "/opt/seagate/cortx/RELEASE.INFO"
