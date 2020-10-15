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

from cortx.utils.security.cipher import Cipher, CipherInvalidToken
import provisioner
import os
import sys
import logging
import string
import secrets

# Update PYTHONPATH to include Provisioner API installed at:
# /usr/local/lib/python3.6/site-packages/cortx-prvsnr-*
sys.path.append(os.path.join('usr', 'local', 'lib',
                             'python3.6', 'site-packages'))


cypher_key = ""
to_decrypt = False
_new_passwd = ""


def encrypt(decrypt=False):
    global to_decrypt, cypher_key, _new_passwd

    pillar_list = __pillar__.keys()
    cluster_id = __grains__['cluster_id']
    _new_passwd = _generate_secret() 

    to_decrypt = decrypt

    for pillar_name in pillar_list:
        cypher_key = Cipher.generate_key(cluster_id, pillar_name)
        _update(__pillar__[pillar_name], pillar_name)

    return True


def _update(data, path):

    for key, val in data.items():
        if isinstance(val, dict):
            data[key] = _update(val, path + '/' + key)
        else:
            if (("secret" in key) or ("password" in key)):
                if not val:
                    val = _new_passwd
                try:
                    temp = Cipher.decrypt(
                        cypher_key, val.encode("utf-8")).decode("utf-8")
                    if to_decrypt:
                        provisioner.pillar_set(path + '/' + key, temp)
                except CipherInvalidToken:
                    val = val.strip('\"')
                    val = val.strip("\'")
                    if to_decrypt:
                        provisioner.pillar_set(path + '/' + key, val)
                    else:
                        provisioner.pillar_set(
                            path + '/' + key,
                            str(Cipher.encrypt(cypher_key,
                                               bytes(val, 'utf8')), 'utf-8')
                        )
    return True


def _generate_secret():

    passwd_strength = 12
    passwd_seed = (string.ascii_letters + string.digits)

    return ''.join(
        [secrets.choice(seq=passwd_seed) for index in range(passwd_strength)]
    )
