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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

from typing import Type
import logging

from ..config import (
    LOCAL_MINION
)

from ..pillar import (
    PillarKey,
    PillarResolver
)

from .. import inputs

from ..vendor import attr

from . import (
    CommandParserFillerMixin
)
from .setup_provisioner import (
    SetupCmdBase
)
from .configure_setup import (
    SetupType
)
from . import (
    destroy_vm,
    destroy_hw,
    grains_get
)

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class Destroy(SetupCmdBase, CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = [
        destroy_vm.run_args_type
    ]

    @staticmethod
    def _nodes():
        nodes = []
        node_list = PillarKey('cluster')
        pillar = PillarResolver(LOCAL_MINION).get([node_list])
        pillar = next(iter(pillar.values()))
        data = pillar[node_list]
        for key in data.keys():
            if 'srvnode' in key:
                nodes.append(key)
        return nodes

    @staticmethod
    def _is_hw():
        key = "hostname_status:Chassis"
        server = grains_get.GrainsGet().run(key,
                                            targets=LOCAL_MINION)
        node = next(iter(server))
        server = server[node][key]
        return server == "server"

    def run(self, **kwargs):

        destroy_args = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(destroy_vm.RunArgsDestroy)
        }
        destroy_args.pop("stages")

        if len(Destroy._nodes()) == 1:
            destroy_args['setup_type'] = SetupType.SINGLE

        if Destroy._is_hw():
            logger.info(
                f"Destroy cortx on {destroy_args['setup_type']} HW setup ")
            destroy_hw.DestroyHW().run(
                **destroy_args
            )
        else:
            logger.info(
                f"Destroy cortx on {destroy_args['setup_type']} VM setup")
            destroy_vm.DestroyNode().run(
                **destroy_args
            )
        logger.info("Done")
