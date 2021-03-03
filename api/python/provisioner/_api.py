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

import sys
import logging

from .salt import auth_init as _auth_init
from .api_spec import api_spec
from .runner import SimpleRunner
from .commands import commands


# TODO
# - cache of pillar files
# - logic of cache update (watchers ?)
# - async API
# - typing
#
# - rollback
# - action might require a set of preliminary steps - hard
#   to describe using generic spec (yaml)

logger = logging.getLogger(__name__)


def auth_init(username, password, eauth='pam'):
    return _auth_init(username, password, eauth=eauth)


def run(command: str, *args, nowait=False, **kwargs):
    # do not expect ad-hoc credentials here
    kwargs.pop('password', None)
    kwargs.pop('username', None)
    kwargs.pop('eauth', None)
    logger.debug(f"Executing command: {command}")
    return SimpleRunner(commands, nowait=nowait).run(command, *args, **kwargs)


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return run(fun, *args, **kwargs)
    return f


mod = sys.modules[__name__]
for fun in api_spec:
    setattr(mod, fun, _api_wrapper(fun))
