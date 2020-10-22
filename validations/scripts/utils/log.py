#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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
#

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging():
    """
    This function set up the logging.
    Default file level logging is set to DEBUG
    """
    global logger
    log_dir = Path("/var/log/seagate/provisioner/")
    if not log_dir.is_dir():
        log_dir.mkdir()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    fileHandler = logging.FileHandler(
        filename='/var/log/seagate/provisioner/validation.log')
    fileHandler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(
        ' %(asctime)sZ - %(levelname)s - %(message)s')
    file_formatter.converter = time.gmtime

    fileHandler.setFormatter(file_formatter)

    logger.addHandler(fileHandler)
    logging.captureWarnings(True)
