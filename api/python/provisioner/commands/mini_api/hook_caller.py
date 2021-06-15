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

import logging

from typing import Union, Optional, List, Dict

from provisioner.vendor import attr
from provisioner import config
from provisioner.salt import function_run
from provisioner.cli_parser import KeyValueListAction

from provisioner.commands._basic import (
    CommandParserFillerMixin,
    RunArgs
)

from .common import MiniAPIParams

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class MiniAPIHook:
    name: str = MiniAPIParams.hook
    flow: Union[config.CortxFlows, str] = MiniAPIParams.flow
    level: Union[config.MiniAPILevels, str] = MiniAPIParams.level


@attr.s(auto_attribs=True)
class HookCaller(CommandParserFillerMixin):
    description = (
        "A mini API helper to call hooks."
    )

    name: str = MiniAPIParams.hook
    flow: Union[config.CortxFlows, str] = MiniAPIParams.flow
    level: Union[config.MiniAPILevels, str] = MiniAPIParams.level
    sw: Optional[List] = MiniAPIParams.sw
    ctx_vars: Optional[Dict] = MiniAPIParams.ctx_vars
    fail_fast: bool = MiniAPIParams.fail_fast
    targets: str = RunArgs.targets

    # helpers
    @classmethod
    def hook(
        cls,
        hook: MiniAPIHook,
        sw: Optional[List] = None,
        ctx_vars: Optional[Dict] = None,
        fail_fast: bool = False,
        targets: str = config.ALL_MINIONS
    ):
        return cls(
            name=hook.name,
            flow=hook.flow,
            level=hook.level,
            sw=sw,
            ctx_vars=ctx_vars,
            fail_fast=fail_fast,
            targets=targets
        ).run()

    # TODO ctx_vars are not fully supported for CLI now
    def __attrs_post_init__(self):
        if isinstance(self.ctx_vars, str):
            self.ctx_vars = self.ctx_vars.split()

        if isinstance(self.ctx_vars, list):
            self.ctx_vars = KeyValueListAction.parse(self.ctx_vars)

    def run(self):
        return function_run(
            'setup_conf.hook',
            fun_kwargs=dict(
                hook=self.name.value,
                flow=self.flow.value,
                level=self.level.value,
                sw=self.sw,
                ctx_vars=self.ctx_vars,
                fail_fast=self.fail_fast
            ),
            targets=self.targets
        )
