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
    config,
    inputs
)
from ..vendor import attr

from .setup_provisioner import (
    Node,
    RunArgsSetup,
    SetupProvisioner
)

from .setup_singlenode import RunArgsSetupSinglenode

logger = logging.getLogger(__name__)


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class RunArgsSetupCluster(RunArgsSetupSinglenode):
    ha: bool = RunArgsSetup.ha
    glusterfs_docker: bool = RunArgsSetup.glusterfs_docker
    srvnode2: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "srvnode-2 host specification",
                'metavar': '[user@]hostname[:port]'
            }
        },
        default='srvnode-2',
        converter=(lambda s: Node.from_spec(f"srvnode-2:{s}"))
    )
    field_setup: bool = attr.ib(init=False, default=False)

    """
    @srvnode2.validator
    def _check_srvnode2(self, attribute, value):
        parts = value.split('@')
        if len(parts) > 2 or len(parts) == 0 or [p for p in parts if not p]:
            raise ValueError(
                f"{attribute.name} should be a valid hostspec [user@]host, "
                f"provided '{value}'"
            )
    """


@attr.s(auto_attribs=True)
class SetupCluster(SetupProvisioner):
    _run_args_type = RunArgsSetupCluster

    def run(self, **kwargs):
        run_args = RunArgsSetupCluster(**kwargs)
        kwargs.pop('srvnode1')
        kwargs.pop('srvnode2')

        setup_ctx = super()._run(
            nodes=[run_args.srvnode1, run_args.srvnode2], **kwargs
        )

        logger.info("Updating hostnames in cluster pillar")
        for node in setup_ctx.run_args.nodes:
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner pillar_set '
                    f'cluster/{node.minion_id}/hostname '
                    f'\'"{node.grains.fqdn}"\''
                ), targets=setup_ctx.run_args.primary.minion_id
            )

        if run_args.config_path:
            logger.info("Updating pillar data using config.ini")
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner configure_setup '
                    f'{config.PRVSNR_PILLAR_CONFIG_INI} '
                    f'{len(setup_ctx.run_args.nodes)}'
                ), targets=setup_ctx.run_args.primary.minion_id
            )
        logger.info("Done")
