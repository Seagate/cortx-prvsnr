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

from logging import exception
from pathlib import Path
from ..command import Command
from provisioner.commands import PillarGet
from provisioner.salt import local_minion_id, function_run
from provisioner.salt import StatesApplier


""" Common functions """

class Commons(Command):
    '''
    Common functions
    '''
    _args = None
    #TODO: Add this path in the global config
    enclosure_id_file_path = "/etc/enclosure-id"

    def fetch_enc_id(self, targets):
        try:
            result = function_run('grains.get', fun_args=['enclosure_id'],
                                targets=targets)
            _enc_id = result[f'{targets}']
        except Exception as exc:
            raise exc
        return _enc_id

    def get_enc_id(self, targets):

        self.logger("Getting enclosure ID")
        _enc_id_file = Path(self.enclosure_id_file_path)

        if _enc_id_file.exists():
            self.logger.info("
            f"Enclosure ID is already generated at {self._enclosure_id_file_path}"
            )
            return fetch_enc_id()
        else:
            self.logger.info("Generating the enclosure ID")
            try:
                _set_enclosure_id_state = "components.system.storage.enclosure_id.config.set"
                StatesApplier.apply(_set_enclosure_id_state, targets)
                return fetch_enc_id()
            except:
                raise exception("Error generating the enclosure ID")
