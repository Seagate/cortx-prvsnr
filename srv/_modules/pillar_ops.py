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

import os
import sys
import logging
import string
import secrets
import provisioner


def _import_cipher():
    from cortx.utils.security import cipher
    return cipher


def encrypt(decrypt=False):

    cipher = _import_cipher()
    pillar_list = __pillar__.keys()
    cluster_id = __grains__['cluster_id']
    new_passwd = _generate_secret()

    for pillar_name in pillar_list:
        cipher_key = cipher.Cipher.generate_key(cluster_id, pillar_name)
        _update(__pillar__[pillar_name], pillar_name,
                cluster_id, new_passwd, cipher, decrypt, cipher_key)

    return True


def _update(data, path, cluster_id, new_passwd, cipher, decrypt, cipher_key):

    for key, val in data.items():
        if isinstance(val, dict):
            data[key] = _update(val, path + '/' + key, cluster_id,
                                new_passwd, cipher, decrypt, cipher_key)
        else:
            if (("secret" in key) or ("password" in key)):
                if not val:
                    val = new_passwd
                try:
                    temp = cipher.Cipher.decrypt(
                        cipher_key, val.encode("utf-8")).decode("utf-8")
                    if decrypt:
                        provisioner.pillar_set(path + '/' + key, temp)
                except cipher.CipherInvalidToken:
                    val = val.strip('\"')
                    val = val.strip("\'")
                    if decrypt:
                        provisioner.pillar_set(path + '/' + key, val)
                    else:
                        provisioner.pillar_set(
                            path + '/' + key,
                            str(cipher.Cipher.encrypt(cipher_key,
                                                      bytes(val, 'utf8')), 'utf-8')
                        )
    return True


def _generate_secret():

    passwd_strength = 12
    passwd_seed = (string.ascii_letters + string.digits)

    return ''.join(
        [secrets.choice(seq=passwd_seed) for index in range(passwd_strength)]
    )
