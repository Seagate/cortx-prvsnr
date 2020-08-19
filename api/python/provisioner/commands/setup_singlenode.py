#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging

from .. import (
    inputs,
    config
)
from ..vendor import attr

from .setup_provisioner import (
    Node,
    RunArgsSetupProvisionerBase,
    SetupProvisioner
)

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSetupSinglenode(RunArgsSetupProvisionerBase):
    srvnode1: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "srvnode-1 host specification",
                'metavar': '[user@]hostname[:port]'
            }
        },
        default=config.LOCALHOST_IP,
        converter=(lambda s: Node.from_spec(f"srvnode-1:{s}"))
    )
    salt_master: str = attr.ib(init=False,  default=None)


@attr.s(auto_attribs=True)
class SetupSinglenode(SetupProvisioner):
    _run_args_type = RunArgsSetupSinglenode

    def run(self, **kwargs):
        run_args = RunArgsSetupSinglenode(**kwargs)
        kwargs.pop('srvnode1')

        setup_ctx = super().run(
            ha=False, nodes=[run_args.srvnode1], **kwargs
        )

        logger.info("Updating hostname in cluster pillar")

        node = setup_ctx.run_args.nodes[0]
        setup_ctx.ssh_client.cmd_run(
            (
                '/usr/local/bin/provisioner pillar_set '
                f'cluster/{node.minion_id}/hostname '
                f'\'"{node.grains.fqdn}"\''
            ), targets=setup_ctx.run_args.primary.minion_id
        )

        logger.info("Done")
