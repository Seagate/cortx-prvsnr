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

from .. import (
    config,
    inputs
)
from ..vendor import attr

from . import (
    CommandParserFillerMixin
)
from .setup_provisioner import (
    RunArgsSetupProvisionerGeneric,
    SetupProvisioner,
    SetupCmdBase
)
from .configure_setup import SetupType

from . import deploy_vm

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class AutoDeployVM(SetupCmdBase, CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = [
        RunArgsSetupProvisionerGeneric,
        deploy_vm.run_args_type
    ]
    description = 'API to deploy Cortx on VM'

    def run(self, nodes, **kwargs):
        setup_provisioner_args = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsSetupProvisionerGeneric)
        }

        deploy_args = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(deploy_vm.run_args_type)
        }

        logger.info(
          "Starting with Provisioner Bootstrapping."
          "\nCommand: setup_provisioner"
        )
        setup_ctx = SetupProvisioner()._run(
            nodes, **setup_provisioner_args
        )

        if setup_provisioner_args.get('config_path'):
            logger.info("Configuring setup using config.ini")
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner configure_setup '
                    f'{config.PRVSNR_PILLAR_CONFIG_INI} '
                    f'{len(nodes)}'
                ), targets=setup_ctx.run_args.primary.minion_id
            )
            setup_ctx.ssh_client.cmd_run(
                (
                    'salt-call state.apply '
                    'system.config.pillar_encrypt'
                ), targets=setup_ctx.run_args.primary.minion_id
            )

            # The ConfStore JSON is required to be generated on all nodes
            # TODO: To be parameterized when addressing EOS-16560
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner confstore_export '
                ), targets=config.ALL_MINIONS
            )

        if len(nodes) == 1:
            deploy_args['setup_type'] = SetupType.SINGLE
        logger.info("Starting: Deployment on VM")
        deploy_vm.DeployVM().run(
            **deploy_args
        )

        logger.info("Done")
