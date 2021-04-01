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

"""Defines a module to set hostname for system"""

import logging
from typing import Type

from . import RunArgsEmpty
from ._basic import CommandParserFillerMixin
from ..vendor import attr
from ..config import LOCAL_MINION
from ..pillar import (
    PillarKey,
    PillarResolver
)
from ..salt import (
    function_run,
    StateFunExecuter,
    local_minion_id
)
from ..errors import SaltError
from .. import inputs

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SetHostname(CommandParserFillerMixin):
    """Defines logic to set hostname for system"""

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsEmpty

    def run(self):
        try:
            logger.info("Fetching server hostname from cluster pillar")
            local_minion = local_minion_id()
            cluster_path = PillarKey('cluster')
            cluster_dict = PillarResolver(local_minion).get([cluster_path])
            cluster_dict = cluster_dict[local_minion][cluster_path]
            server_hostname = cluster_dict[local_minion]['hostname']
            if not server_hostname or server_hostname is values.MISSED::
                logger.error("Failed to get hostname from cluster pillar")
                raise ValueError("Failed to get hostname from cluster pillar")

            logger.info(f"Setting hostname to {server_hostname}")
            StateFunExecuter.execute(
                'network.system',
                fun_kwargs=dict(
                    name='set_hostname',
                    hostname=server_hostname,
                    apply_hostname=True,
                    retain_settings=True
                ),
                targets=LOCAL_MINION
            )
        except Exception as exc:
            raise exc
        logger.info("Hostname set successfully")
