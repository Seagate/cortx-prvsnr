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

from cortx_setup.commands.command import Command
from provisioner.salt import (
    local_minion_id,
    StatesApplier,
    function_run
)
from provisioner.config import (
    PRVSNR_PILLAR_DIR
)
from provisioner.utils import dump_yaml
from pathlib import Path
from cortx.utils.conf_store import Conf

class NodePrepareFirewall(Command):
    _args = {
        'config': {
            'type': str,
            'optional': True}
    }

    def run(self, **kwargs):

        node_id = local_minion_id()
        firewall_pillar_sls = Path(f"{PRVSNR_PILLAR_DIR}/components/firewall.sls")

        self.logger.debug(f"updating firewall config on {node_id}")

        try:
            self.logger.debug(f"loading firewall configuration")
            firewall_config_arg = kwargs.get('config')
            Conf.load('index1', firewall_config_arg)
            firewall_conf = {'firewall': Conf.get('index1','firewall') }
            dump_yaml(firewall_pillar_sls, dict(firewall_conf))

            function_run('saltutil.refresh_pillar', targets=node_id)

            self.logger.debug(f"Applying 'components.system.firewall' on {node_id}")
            StatesApplier.apply(
                ["components.system.firewall"],
                local_minion_id()
            )
        except Exception as ex:
            raise ex
        self.logger.debug("Done")
