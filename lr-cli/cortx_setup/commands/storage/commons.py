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

import hashlib
import json
import requests
from logging import exception
from ..command import Command
from pathlib import Path
from provisioner.salt import function_run
from provisioner.salt import StatesApplier

class Commons(Command):
    '''
    Common functions
    '''
    _args = None
    #TODO: Add this path in the global config
    _enclosure_id_file_path = "/etc/enclosure-id"

    def fetch_enc_id(self, targets=None):
        try:
            result = function_run('grains.get', fun_args=['enclosure_id'],
                                targets=targets)
            _enc_id = result[f'{targets}']
        except Exception as exc:
            raise exc
        return _enc_id

    def get_enc_id(self, targets=None, force=False):

        self.logger.info("Getting enclosure ID")
        _enc_id_file = Path(self._enclosure_id_file_path)

        if _enc_id_file.exists() and force is False:
            self.logger.info(
            f"Enclosure ID is already generated at {self._enclosure_id_file_path}"
            )
            return self.fetch_enc_id(targets)
        else:
            self.logger.info("Generating the enclosure ID")
            try:
                _set_enclosure_id_state = "components.system.storage.enclosure_id.config.set"
                StatesApplier.apply(_set_enclosure_id_state, targets)
                return self.fetch_enc_id(targets)
            except:
                raise exception("Error generating the enclosure ID")


class EnclosureInfo(Command):

    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.headers = {"datatype": "json"}
        self.url = "http://" + self.host + ":" + str(self.port) + "/api/"

    def connect_enclosure(self):
        user_pass = f"{self.username}_{self.password}"
        user_pass = bytes(user_pass, 'utf-8')
        auth_string = hashlib.sha256(user_pass).hexdigest()
        response = json.loads(requests.get(self.url + 'login/' + auth_string, headers=self.headers).content)
        return response

    def connection_status(self):
        response = self.connect_enclosure()
        return (len(response['status']) == 1 and response["status"][0]["return-code"] == 1)

    def get_enclosure_serial(self):
        response = self.connect_enclosure()

        if len(response['status']) == 1 and response["status"][0]["return-code"] == 1:
            self.headers['sessionKey'] = response['status'][0]['response']
        else:
            self.logger.error("Controller is unreachable with the current credentials! Please provide valid username and password")
            raise Exception("Wrong inputs provided")

        show_system_response = json.loads(requests.get(self.url + 'show/system', headers=self.headers).content)

        if len(show_system_response['system']) == 1 and show_system_response['status'][0]['return-code'] == 0:
            return show_system_response['system'][0]['midplane-serial-number']
        else:
            self.logger.error("midplane-serial-number not found!")
