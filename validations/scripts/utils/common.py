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
import subprocess
import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/utils")


logger = logging.getLogger(__name__)


def run_subprocess_cmd(cmd, **kwargs):
    _kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    _kwargs.update(kwargs)
    _kwargs['check'] = True

    if not _kwargs.get('timeout', None):
        _kwargs['timeout'] = 15
    if type(cmd) is str:
        cmd = cmd.split()

    try:
        logger.debug(f"Subprocess command {cmd}, kwargs: {_kwargs}")
        res = subprocess.run(cmd, **_kwargs)
    except subprocess.TimeoutExpired as exc:
        result = (1, str(exc), repr(exc))
    except Exception as exc:
        result = (1, str(exc), repr(exc))
    else:
        logger.debug(f"Subprocess command resulted in: {res}")
        result = (res.returncode, res.stdout, res.stderr)
    return result
