#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
    SetupProvisioner
)

from .configure_setup import SetupType


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SetupCortx(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = [
        RunArgsSetupProvisionerGeneric
    ]

    def run(self, nodes, **kwargs):
        setup_provisioner_args = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsSetupProvisionerGeneric)
        }

        setup_ctx = SetupProvisioner().run(nodes, **setup_provisioner_args)

        # FIXME setup type is not DUAL, need generic solution
        if setup_provisioner_args.config_path and False:
            raise NotImplementedError(
                "ini file configuration is not yet supported "
                "for setup cortx command"
            )

            logger.info("Updating pillar data using config.ini")
            setup_ctx.ssh_client.cmd_run(
                (
                    '/usr/local/bin/provisioner configure_setup '
                    f'{config.PRVSNR_PILLAR_CONFIG_INI} {SetupType.DUAL.value}'
                ), targets=setup_ctx.run_args.primary.minion_id
            )
        logger.info("Done")
