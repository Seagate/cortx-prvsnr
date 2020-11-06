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

# How to test:
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call lyveutil.decrypt "component" "secret"

from salt import client


def decrypt(component, secret):
    """ Decrypt secret.

    Args:
      secret: Secret to be decrypted.
    """
    from cortx.utils.security.cipher import Cipher, CipherInvalidToken
    
    retval = None
    cluster_id = __grains__['cluster_id']
    cipher_key = Cipher.generate_key(cluster_id, component)

    if secret:
        retval = (Cipher.decrypt(cipher_key, secret.encode("utf-8"))).decode("utf-8")
      
    return retval
