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

# Python API to generate roster file required for salt-ssh
import logging
import subprocess
import time
from typing import Type

from ..utils import run_subprocess_cmd
from .. import (
    inputs
)
from ..vendor import attr

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ClusterFormation(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    description = "API to generate config.ini file from given params"

    def run(self, **kwargs):

        res = run_subprocess_cmd("salt-key -L")
        logger.info(f"List of unaccepted minions {res.stdout}")

        logger.info(f"Accepting all salt-minions to form cluster")
        res = subprocess.run("echo Y | salt-key -A", shell=True)
        if res.returncode == 0:
            logger.info(f"Successfully formed salt cluster")
        logger.info(f"Verify cluster formed")
        time.sleep(30)
        res = subprocess.run("salt '*' test.ping", shell=True)
        if res.returncode == 0:
            logger.info("cluster status: Success")
        else:
            logger.info("cluster status: Failed")
