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
from cortx_setup.commands.storage.enclosure_info import EnclosureInfo
from cortx_setup.config import CONFSTORE_CLUSTER_FILE
from cortx_setup.commands.common_utils import get_pillar_data
from provisioner.commands import PillarSet
from provisioner.salt import local_minion_id
from cortx.utils.conf_store import Conf
from cortx.utils.security.cipher import Cipher

node_id = local_minion_id()
enc_num = "enclosure-" + ((node_id).split('-'))[1]

enc_id_on_node = get_pillar_data(
    f'storage/{enc_num}/enclosure_id'
)

class NodePrepareStorage(Command):
    """Cortx Setup API for Preparing Storage in field"""
    _args = {
        'user': {
            'type': str,
            'default': None,
            'optional': True
        },
        'password': {
            'type': str,
            'default': None,
            'optional': True
        }
    }

    def decrypt_passwd(self, encr_pass):
        """Returns decrypted password"""

        _component = "storage"
        try:
            cipher_key = Cipher.generate_key(enc_id_on_node, _component)
            return (
                Cipher.decrypt(
                    cipher_key, encr_pass.encode("utf-8")
                )
            ).decode("utf-8")
        except Exception as exc:
            self.logger.error(
                "Could not decrypt the password stored in the configuration\n"
            )
            raise exc

    def validate_credentials(self, user=None, passwd=None):
        """
            Compares user and password values provided by the user as input to
            that of the user and password values present in the pillar.
        """

        self.logger.debug(
            f"Validating the provided credentials ({user}/{passwd})"
        )
        _ctrl_user = get_pillar_data(
            f'storage/{enc_num}/controller/user'
        )
        _ctrl_secret_enc = get_pillar_data(
            f'storage/{enc_num}/controller/secret'
        )

        # Decrypt the secret read from the storage pillar

        if not enc_id_on_node:
            self.logger.error(
                "Could not fetch enclosure_id id from pillar"
            )
            raise ValueError("Enclosure ID is not set on node")

        _ctrl_secret = self.decrypt_passwd(_ctrl_secret_enc)

        _user_check = True
        _passwd_check = True

        if user != _ctrl_user:
            self.logger.warning(
                f"Username provided {user} does not match"
                " with the user name in configuration"
            )
            _user_check = False
        else:
            self.logger.debug(
                f"Username provide {user} matches with"
                " the user name in configuration"
            )

        if passwd != _ctrl_secret:
            self.logger.warning(
                f"The password provided ({passwd}) does not match"
                " with the password in configuration"
            )
            _passwd_check = False
        else:
            self.logger.debug(
                f"Password provided ({passwd}) matches with"
                " the password in configuration"
            )

        if not _user_check or not _passwd_check:
            return False

        return True


    def run(self, **kwargs):
        """
        Execution:
        `cortx_setup node prepare storage --user <user> --password <password>`
        """

        _enc_user = kwargs.get('user')
        _enc_passwd = kwargs.get('password')

        try:
            self.validate_credentials(_enc_user, _enc_passwd)

            # Fetch enclosure id from the enclosure
            # This will use the user/password from pillar
            # and keep the enclosure id in /etc/enclosure-id
            # TODO: use the credentials provided by user
            _enc_ip = get_pillar_data(
                f'storage/{enc_num}/controller/primary/ip',
            )
            _enc_port = get_pillar_data(
                f'storage/{enc_num}/controller/primary/port',
            )

            _enc_id_on_enc = EnclosureInfo(_enc_ip, _enc_user, _enc_passwd, _enc_port).fetch_enclosure_serial()
        except Exception as e:
            self.logger.error(
                f"Could not fetch the enclosure id:\n"
                f"Possible reasons:\n"
                f"1. User name or password provided are not correct.\n"
                f"   Please rerun the command with correct credentials.\n"
                f"2. The storage enclosure connected to the node is\n"
                f"   different than the one that was used in factory.\n"
                "    You can either connect the correct enclosure and"
                "    try again or rerun the following command to use"
                f"   this enclosure with node henceforth:\n"
                "    cortx_setup storage config --user <user> --password <pass>"
            )
            raise e

        # Compare the enclosure id fetched from the enclosure with the
        # one generated in factory (and stored in grains).
        if _enc_id_on_enc != enc_id_on_node:
            self.logger.warning(
                "The enclosure id from enclosure don't match with"
                " the enclosure id stored on the node"
            )
            self.logger.warning(
                "The storage enclosure connected to the node seems to be"
                " different than the one that was used in factory."
            )
            self.logger.info(
                "Updating the new enclosure id on the node"
            )
            self.logger.debug(
                f"Updating the enclosure id {_enc_id_on_enc} in pillar"
            )
            PillarSet().run(
                f'storage/{enc_num}/enclosure_id',
                _enc_id_on_enc,
                local=True
            )
            self.logger.debug(
                f"Updating the enclosure id {_enc_id_on_enc} in confstore"
            )
            try:
                self.load_conf_store(
                    'node_info_index',
                    f'json://{CONFSTORE_CLUSTER_FILE}'
                )
            except Exception:
                self.logger.debug("index already present, using the same")
            Conf.set(
                'node_info_index',
                f'storage_enclosure>enclosure_id',
                _enc_id_on_enc
            )
            Conf.save('node_info_index')

        else:
            self.logger.info(
                "Enclosure ID fetched from enclosure matches with the"
                " one stored on the node"
            )

        #TODO: Configure storage by LUN identification, segregation
        #  based on priority/affinity to controller and partition for metadata.
        #configure_storage()

        self.logger.info("Done")
