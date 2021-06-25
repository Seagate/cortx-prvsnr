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


from cortx_setup.commands.command import Command
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx.utils.conf_store import Conf
from provisioner.salt import StateFunExecuter


class PrepareConfstore(Command):
    _args = {}

    def run(self):
        """Prepare confstore in factory.
           cortx_setup prepare_confstore
        """

        template_file_path = str(CONFSTORE_CLUSTER_FILE.parent / 'factory_confstore_template')

        Conf.load(
            'node_config_index',
            f'json://{CONFSTORE_CLUSTER_FILE}'
        )

        StateFunExecuter.execute(
            'file.managed',
            fun_kwargs=dict(
                name=template_file_path,
                source='salt://components/system/files/factory_confstore_template.j2',
                template='jinja'))
        template_data = ""
        with open(template_file_path, 'r') as f:
            template_data = f.read().splitlines()

        for data in template_data:
            if data:
                key, value = data.split("=")
                Conf.set('node_config_index', key, value)

        Conf.save('node_config_index')
        self.logger.debug("Done")
