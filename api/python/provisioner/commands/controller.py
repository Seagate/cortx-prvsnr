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

import json
import requests
import logging

from .. import (
    config,
    inputs
)
from ..vendor import attr

from . import (
    CommandParserFillerMixin
)

from ..salt import (
    function_run,
    cmd_run,
    StatesApplier,
    local_minion_id,
    sls_exists
)

from ..utils import get_pillar_data

# @attr.s(auto_attribs=True)
# class RunArgsController:
#     user_name: str = attr.ib(
#         metadata={
#             inputs.METADATA_ARGPARSER: {
#                 'help': "User name to login to Controller"
#             }
#         }
#     )
#     password: str = attr.ib(
#         metadata={
#             inputs.METADATA_ARGPARSER: {
#                 'help': "Password for the user to login to Controller"
#             }
#         }
#     )    
#     mc_primary_host: str = attr.ib(
#         metadata={
#             inputs.METADATA_ARGPARSER: {
#                 'help': "Hostname/IP of primary controller"
#             }
#         }, default="10.0.0.2"
#     )
#     mc_secondary_host: str = attr.ib(
#         metadata={
#             inputs.METADATA_ARGPARSER: {
#                 'help': "Hostname/IP of secondary controller"
#             }
#         },
#         default="10.0.0.3"
#     )

#     dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class Controller:

    def url(self,api):
        return "http://" + self.mc_primary_host + ":" + wsport + api

    def get_request(url,headers,timeout=20):
        return requests.get(url,headers,timeout)

    def login(self):
        login = "/api/login/"
        auth = self.mc_user + '_' + self.passwd
        timeout = 20
        url = self.url(self.URI_CLIAPI_LOGIN)

        auth_hash = hashlib.sha256(cli_api_auth.encode('utf-8')).hexdigest()

        response = self.get_request(url+auth_hash,headers,timeout)
        if not response or response.status_code != 200:
            logger.error("Login Failed to Controller")

        session_key = json.loads(response.content)['status'][0]['response']
        self.headers["sessionKey"] = session_key
        logger.info("Sucessfully logged in to controller")



    def __entry__(self):
        self.local_minion = local_minion_id()
        _enclosure_id = get_pillar_data("cluster/"+self.local_minion+"/storage/enclosure_id")
        self.mc_primary_host = get_pillar_data("storage/"+_enclosure_id+"/controller/primary/ip")
        self.mc_secondary_host = get_pillar_data("storage/"+_enclosure_id+"/controller/secondary/ip")
        
        self.mc_user = get_pillar_data("storage/"+_enclosure_id+"/controller/user")
        self.passwd = get_pillar_data("storage/"+_enclosure_id+"/controller/secret")

        decrypt_cmd = 'salt-call lyveutil.decrypt storage {passwd} --output=newline_values_only'
        self.passwd = cmd_run(cmd.format(passwd = self.passwd), targets=self.local_minion)[self.local_minion]
        self.headers = {'datatype':'json',"sessionKey":None}
        self.login()


    def __exit__(self):
        logout = "/api/logout/"
        url = self.url(logout)
        response = self.get_request(url,headers,timeout)
        if response.status_code == 200:
            logger.info("Logged out of Enclosure")


@attr.s(auto_attribs=True)
class ShowVolumeMaps(CommandParserFillerMixin):

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsBase

    def run(self,target_ctrl: str = CONTROLLER_BOTH):
        response = None
        with Controller as ctrl:
            api = "api/show/volume-maps/"
            url = ctrl.url(api)
            response = get_request(url,ctrl.headers)
            if response.status_code != 200:
                logger.error("Error fetching volume maps")
        return json.loads(response.content)
            
        

        




    

