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
import importlib
import site

from ..config import (
    PRVSNR_PILLAR_CONFIG_INI,
    GroupChecks,
    ALL_MINIONS
)
from .. import inputs

from ..vendor import attr

from . import (
    CommandParserFillerMixin
)
from .setup_provisioner import (
    RunArgsSetupProvisionerGeneric,
    SetupProvisioner,
    SetupCmdBase
)
from . import check
from . import deploy_dual

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class AutoDeploy(SetupCmdBase, CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = [
        RunArgsSetupProvisionerGeneric,
        deploy_dual.run_args_type
    ]

    @staticmethod
    def deployment_validations(deploy_check):

        # even if cortx-py-util package is installed during runtime
        # it failed to import, reload of site pkg helped here
        importlib.reload(site)

        check_import = importlib.reload(check)

        check_cmd = check_import.Check

        try:
            check_res = check_cmd().run(deploy_check)
        except Exception as exc:
            logger.error("Deployment Failed.\n")
            raise ValueError("Error During Deployment "
                             f"{deploy_check} Validations: {str(exc)}")
        else:
            if deploy_check == GroupChecks.DEPLOY_PRE_CHECKS.value:
                check_import.PreChecksDecisionMaker().make_decision(
                    check_result=check_res)
            elif deploy_check == GroupChecks.DEPLOY_POST_CHECKS.value:
                check_import.PostChecksDecisionMaker().make_decision(
                    check_result=check_res)
            else:
                logger.error(
                  "Deployment Failed. Please provide a proper Check name"
                )
                raise ValueError(
                    f'Group Check "{deploy_check}" is not supported')

    def run(self, nodes, **kwargs):
        setup_provisioner_args = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsSetupProvisionerGeneric)
        }

        deploy_args = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(deploy_dual.run_args_type)
        }

        logger.info("Starting with Setup Provisioner")
        setup_ctx = SetupProvisioner()._run(
            nodes, **setup_provisioner_args
        )

        if setup_provisioner_args.get('config_path'):
            logger.info("Configuring setup using config.ini")
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner configure_setup '
                    f'{PRVSNR_PILLAR_CONFIG_INI} '
                    f'{len(nodes)}'
                ), targets=setup_ctx.run_args.primary.minion_id
            )
            setup_ctx.ssh_client.cmd_run(
                (
                    'salt-call state.apply '
                    'components.system.config.pillar_encrypt'
                ), targets=setup_ctx.run_args.primary.minion_id
            )

            # The ConfStore JSON is required to be generated on all nodes
            # TODO: To be parameterized when addressing EOS-16560
            setup_ctx.ssh_client.cmd_run(
                (
                    'provisioner pillar_export '
                ), targets=ALL_MINIONS
            )

        logger.info("Deployment Pre-Flight Validations")
        self.deployment_validations(GroupChecks.DEPLOY_PRE_CHECKS.value)

        logger.info("Deploy")
        deploy_dual.DeployDual(setup_ctx=setup_ctx).run(
            **deploy_args
        )

        logger.info("Post-Deployment Validations")
        self.deployment_validations(GroupChecks.DEPLOY_POST_CHECKS.value)

        logger.info("Done")
