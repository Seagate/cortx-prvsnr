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
from scripts.utils.pillar_get import PillarGet
from scripts.utils.bmc import BMCValidations
from scripts.utils.common import *
from messages.user_messages import *
logger = logging.getLogger(__name__)

class UnboxingValidationsCall():

    def __init__(self):
        ''' Validations for Pre-Unboxing
        '''
        self.bmc = BMCValidations()
        pass

    def check_controller_mc_accessible(self):
        ''' Validations for Controllers accessibility
        '''
        logger.info("Validations for Controllers accessibility")

        response = {}
        ctrls = ['primary_mc', 'secondary_mc']
        for ctrl in ctrls:
            logger.info(f"Get controller IP for '{ctrl}'.")
            ctrl_ip = PillarGet.get_pillar(f"storage_enclosure:controller:{ctrl}:ip")
            if ctrl_ip['ret_code']:
                logger.error(f"Failed to get controller IP. Response : '{ctrl_ip}'")
                return ctrl_ip
            logger.info(f"Received controller IP for '{ctrl}' successfully.")

            logger.info(f"Get controller user for '{ctrl}'.")
            user = PillarGet.get_pillar(f"storage_enclosure:controller:user")
            if user['ret_code']:
                logger.error(f"Failed to get controller user. Response : '{user}'")
                return user
            logger.info(f"Received controller user for '{ctrl}'.")

            logger.info(f"Get controller secret for '{ctrl}'.")
            enc_secret = PillarGet.get_pillar(f"storage_enclosure:controller:secret")

            if enc_secret['ret_code']:
                logger.error(f"Failed to get controller secret. Response : '{enc_secret}'")
                return enc_secret
            logger.info(f"Received controller secret for '{ctrl}'.")
            logger.info(f"Decrypt controller secret for '{ctrl}'.")
            get_decrypt_secret = decrypt_secret("storage_enclosure", enc_secret["response"])

            if get_decrypt_secret['ret_code']:
                logger.error(f"Failed to decrypt secret. Response : '{get_decrypt_secret}'")
                return get_decrypt_secret
            logger.info(f"Decrypted controller secret for '{ctrl}' successfully.")

            logger.info(f"Checking SSH connection.")
            response = ssh_remote_machine(hostname=ctrl_ip["response"],
                                          username=user["response"],
                                          password=get_decrypt_secret["response"])
            if response['ret_code']:
                logger.error(f"SSH connection failed.")
                return response

        response['message'] = "Both Controller MC are accessible."
        return response

    def check_bmc_stonith_config(self):
        ''' Validations for BMC STONITH
        '''
        logger.info("Validations for BMC STONITH")

        logger.info(f"Get node list.")
        node_res = PillarGet.get_pillar("cluster:node_list")
        if node_res['ret_code']:
            return node_res

        nodes = node_res['response']
        for node in nodes:
            logger.info(f"Get BMC IP.")
            bmc_ip_get = PillarGet.get_pillar(f"cluster:{node}:bmc:ip")
            if bmc_ip_get['ret_code']:
                logger.error(f"Failed to get BMC IP.")
                return bmc_ip_get

            logger.info(f"Get BMC user.")
            user = PillarGet.get_pillar(f"cluster:{node}:bmc:user")
            if user['ret_code']:
                logger.error(f"Failed to get BMC user.")
                return user

            logger.info(f"Get BMC secret.")
            secret = PillarGet.get_pillar(f"cluster:{node}:bmc:secret")
            if secret['ret_code']:
                logger.error(f"Failed to get BMC secret.")
                return secret

            logger.info(f"Decrypt BMC secret.")
            decrypt_passwd = decrypt_secret("cluster", secret["response"])
            if decrypt_passwd['ret_code']:
                logger.error(f"Failed to decrypt BMC secret.")
                return decrypt_passwd

            bmc_ip = bmc_ip_get["response"]
            bmc_user = user["response"]
            bmc_passwd = decrypt_passwd["response"]
            bmc_stonith_check = self.bmc.bmc_stonith_config(bmc_ip, bmc_user, bmc_passwd)
            if bmc_stonith_check['ret_code']:
                bmc_stonith_check["message"]= str(BMC_STONITH_ERROR)
                return bmc_stonith_check

        bmc_stonith_check["message"]= str(BMC_STONITH_CHECK)
        return bmc_stonith_check
