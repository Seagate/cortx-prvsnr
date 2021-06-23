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
from typing import Type, List, Union

from provisioner import inputs, config
from provisioner.attr_gen import attr_ib
from provisioner.errors import SWUpdateError
from provisioner.pillar import PillarKey, PillarResolver
from provisioner.salt import StatesApplier, local_minion_id
from provisioner.vendor import attr
from provisioner.commands._basic import (
    RunArgs, RunArgsBase, CommandParserFillerMixin
)
from provisioner.commands.release import (
    GetRelease
)
from provisioner.commands.mini_api import (
    HookCaller,
    MiniAPIHook
)

from .get_swupgrade_info import GetSWUpgradeInfo

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSWUpgradeNode(RunArgsBase):
    flow: Union[config.CortxFlows, str] = attr_ib(
        cli_spec='mini_api/flow',
        validator=attr.validators.in_(config.CortxFlows),
        converter=config.CortxFlows
    )
    targets: str = RunArgs.targets
    sw: List = attr_ib(
        cli_spec='upgrade/provisioner/sw', default=None
    )
    no_hooks: bool = attr_ib(
        cli_spec='upgrade/provisioner/no_hooks', default=False
    )


@attr.s(auto_attribs=True)
class SWUpgradeNode(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSWUpgradeNode

    def validate(self):
        # TODO node level validation
        # logger.info('SW Upgrade Node Validation')
        pass

    def plan_upgrade(self, sw_list=None):
        if sw_list is None:
            pi_key = PillarKey('upgrade/sw_list')
            sw_list = PillarResolver(local_minion_id()).get(
                [pi_key], fail_on_undefined=True
            )[local_minion_id()][pi_key]
            logger.debug(f"Resolved sw list: {sw_list}")

        # TODO plan the sw order
        #   - (if not provided) plan according to upgrade ISO data
        pi_key = PillarKey('commons/sw_data')
        sw_data = PillarResolver(local_minion_id()).get(
            [pi_key], fail_on_undefined=True
        )[local_minion_id()][pi_key]
        logger.debug(f"Resolved sw data: {sw_data}")

        diff = set(sw_list) - set(sw_data)
        if diff:
            raise ValueError(f"Unexpected sw to upgrade: {diff}")

        sw_data = {
            _sw: _data for _sw, _data in sw_data.items()
            if _sw in sw_list
        }

        # FIXME return list of objects, e.g. SWData
        return sw_data

    def backup(self, flow, no_hooks=False, targets=config.ALL_TARGETS):
        if not no_hooks:
            logger.info("Trigger 'backup' hook (node level)")
            mini_hook = MiniAPIHook(
                name=config.MiniAPIHooks.BACKUP,
                flow=flow,
                level=config.MiniAPILevels.NODE
            )
            HookCaller.hook(mini_hook, targets=targets)

    def upgrade_sw(self, sw, sw_data, targets):
        logger.info(f"Upgrading/Installing '{sw}' on '{targets}'")
        # FIXME hard-coded
        StatesApplier.apply([f"{sw_data['base_sls']}.install"], targets)

    def upgrade(
        self, sw_data, flow, no_hooks=False, targets=config.ALL_TARGETS
    ):
        # FIXME what if the following returns different versions
        #       than cluster level logic
        cortx_version = GetRelease.cortx_version()
        upgrade_version = GetSWUpgradeInfo.cortx_version()
        ctx_vars = dict(
            CORTX_VERSION=cortx_version,
            CORTX_UPGRADE_VERSION=upgrade_version
        )

        mini_hook = MiniAPIHook(
            name=config.MiniAPIHooks.PRE_UPGRADE,
            flow=flow,
            level=config.MiniAPILevels.NODE
        )

        if not no_hooks:
            logger.info("Fire pre-upgrade event (node level)")
            HookCaller.hook(
                mini_hook, ctx_vars=ctx_vars, targets=targets
            )

        logger.info(f"Upgrading sw: '{list(sw_data)}'")
        for sw, data in sw_data.items():
            self.upgrade_sw(sw, data, targets)

        if not no_hooks:
            logger.info("Fire post-upgrade event (node level)")
            mini_hook.name = config.MiniAPIHooks.POST_UPGRADE
            HookCaller.hook(
                mini_hook, ctx_vars=ctx_vars, targets=targets
            )

    def run(self, flow, sw=None, no_hooks=False, targets=config.ALL_TARGETS):
        try:
            # ASSUMPTIONS:
            #   - local minion has already upgraded version of provisioner
            #   - local minion has the same version of ISO

            logger.info(
                f"SW Upgrade Node, sw '{sw or 'all'}',"
                f" no_hooks '{no_hooks}', targets '{targets}'"
            )

            self.validate()

            sw_data = self.plan_upgrade(sw_list=sw)

            self.backup(flow, no_hooks=no_hooks, targets=targets)

            self.upgrade(sw_data, flow, no_hooks=no_hooks, targets=targets)

        except Exception as update_exc:
            # TODO TEST
            # Note. rollback is not considered for R2
            logger.exception('SW Upgrade Node failed')
            raise SWUpdateError(update_exc) from update_exc
