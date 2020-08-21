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
    config,
    inputs
)
from ..vendor import attr

from .setup_provisioner import (
    Node,
    RunArgsSetup,
    SetupProvisioner
)

from .configure_setup import SetupType
from .setup_singlenode import RunArgsSetupSinglenode


logger = logging.getLogger(__name__)


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class RunArgsSetupCluster(RunArgsSetupSinglenode):
    ha: bool = RunArgsSetup.ha
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

        setup_ctx = super().run(
            nodes=[run_args.srvnode1, run_args.srvnode2], **kwargs
        )

        logger.info("Updating hostnames in cluster pillar")
        for node in setup_ctx.run_args.nodes:
            setup_ctx.ssh_client.cmd_run(
                (
                    '/usr/local/bin/provisioner pillar_set '
                    f'cluster/{node.minion_id}/hostname '
                    f'\'"{node.grains.fqdn}"\''
                ), targets=setup_ctx.run_args.primary.minion_id
            )

        if run_args.config_path:
            logger.info("Updating pillar data using config.ini")
            setup_ctx.ssh_client.cmd_run(
                (
                    '/usr/local/bin/provisioner configure_setup '
                    f'{config.PRVSNR_PILLAR_CONFIG_INI} {SetupType.DUAL.value}'
                ), targets=setup_ctx.run_args.primary.minion_id
            )
        logger.info("Done")
