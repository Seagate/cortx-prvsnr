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

import os
import logging
import logging.handlers


class Log:
    logger = None

    @staticmethod
    def _get_logger(file_name, log_level, log_path: str):
        log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
        logger_name = f"{file_name}"

        formatter = logging.Formatter(log_format, "%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger(logger_name)
        log_file = os.path.join(log_path, f"{file_name}.log")

        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

        file_handler = logging.handlers.RotatingFileHandler(log_file, mode="a")

        c_handler.setFormatter(c_format)
        file_handler.setFormatter(formatter)

        logger.setLevel(logging.DEBUG)
        c_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(c_handler)

        Log.logger = logger
