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
from typing import Type, List

from provisioner import inputs, config
from provisioner.attr_gen import attr_ib
from provisioner.errors import SWUpdateError
from provisioner.pillar import PillarKey, PillarResolver
from provisioner.salt import StatesApplier, local_minion_id
from provisioner.vendor import attr
from provisioner.commands._basic import RunArgsBase, CommandParserFillerMixin

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSWUpgradeNode(RunArgsBase):
    sw: List = attr_ib(
        cli_spec='upgrade/provisioner/sw', default=None
    )


@attr.s(auto_attribs=True)
class SWUpgradeNode(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSWUpgradeNode

    def validate(self):
        # TODO node level validation
        # logger.info('SW Upgrade Node Validation')
        pass

    def plan_upgrade(self, sw=None):
        # TODO plan the sw order
        #   - (if not provided) plan according to upgrade ISO data
        pi_key = PillarKey('upgrade/sw_list')
        sw_list = PillarResolver(local_minion_id()).get(
            [pi_key], fail_on_undefined=True
        )
        sw_list = sw_list[local_minion_id()][pi_key]
        logger.debug(f"Resolved sw list: {sw_list}")

        if sw:
            sw_list = {
                _sw: _data for _sw, _data in sw_list.items()
                if _sw in sw
            }

        # FIXME return list of objects, e.g. SWData
        return sw_list

    def backup(self):
        # TODO node level backup
        # logger.info('SW Upgrade Node Backup (node level)')
        pass

    def upgrade_sw(self, sw, sw_data, targets):
        logger.info(f"Upgrading/Installing '{sw}' on '{targets}'")
        StatesApplier.apply([f"{sw_data['sls']}.install"], targets)

    def upgrade(self, sw_list, targets=config.ALL_TARGETS):
        logger.info("Fire pre-upgrade event (node level)")
        # FIXME pre-upgrade calls
        logger.info('SW Upgrade Node (node level)')

        for sw, sw_data in sw_list.items():
            self.upgrade_sw(sw, sw_data, targets)

        logger.info("Fire post-upgrade event (node level)")
        # FIXME post-upgrade calls

    def run(self, sw=None, targets=config.ALL_TARGETS):
        try:
            # ASSUMPTIONS:
            #   - local minion has already upgraded version of provisioner
            #   - local minion has the same version of ISO

            self.validate()

            sw_list = self.plan_upgrade(sw=sw)

            self.backup()

            self.upgrade(sw_list, targets=targets)

        except Exception as update_exc:
            # TODO TEST
            logger.exception('SW Upgrade Node failed')
            raise SWUpdateError(update_exc) from update_exc
