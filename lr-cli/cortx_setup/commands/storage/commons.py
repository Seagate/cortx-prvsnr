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
    enclosure_id_file_path = "/etc/enclosure-id"

    def fetch_enc_id():
        # Check if file /etc/enclosure-id has correct content:
        # 1. has only one line and
        # 2. has only one word - enclosure serial.

        self.logger.info("Fetching the enclosure ID from {self._enclosure_id_file_path}")       
        _enc_id_file = Path(self.enclosure_id_file_path)
        _words = None
        with open(_enc_id_file) as _fp:
            _line_cnt = 0
            for _line in _fp:
                self.logger.info(f"content of line {_line_cnt}: {_line}")
                _words = _line.strip()
                _line_cnt += 1

        if _words and (_line_cnt == 1):
            _n_words = 1
            for id in _words:
                if id == " ":
                    _n_words += 1
            if _n_words == 1:
                return id

        msg = ("ERROR: The contents of {self.enclosure_id_file_path}"
            "looks incorrect, failing"
        )
        self.logger.error(msg)
        raise Exception(msg)

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
        
