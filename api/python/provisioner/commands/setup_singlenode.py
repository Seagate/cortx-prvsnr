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

        setup_ctx = super()._run(
            ha=False, nodes=[run_args.srvnode1], **kwargs
        )

        logger.info("Updating hostname in cluster pillar")

        node = setup_ctx.run_args.nodes[0]
        setup_ctx.ssh_client.cmd_run(
            (
                'provisioner pillar_set '
                f'cluster/{node.minion_id}/hostname '
                f'\'"{node.grains.fqdn}"\''
            ), targets=setup_ctx.run_args.primary.minion_id
        )

        logger.info("Updating pillar data using config.ini")
        setup_ctx.ssh_client.cmd_run(
            (
                'provisioner configure_setup '
                f'{config.PRVSNR_PILLAR_CONFIG_INI} '
                f'{len(setup_ctx.run_args.nodes)}'
            ), targets=setup_ctx.run_args.primary.minion_id
        )
        logger.info("Done")
