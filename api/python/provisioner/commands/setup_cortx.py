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
