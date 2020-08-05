#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

# How to test:
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call lyveutil.decrypt "component" "secret"

from salt import client

from eos.utils.security.cipher import Cipher, CipherInvalidToken

def decrypt(component, secret):
    """ Decrypt secret.

    Args:
      secret: Secret to be decrypted.
    """
    retval = None
    cluster_id = __grains__['cluster_id']
    cipher_key = Cipher.generate_key(cluster_id, component)

    if secret:
        retval = (Cipher.decrypt(cipher_key, secret.encode("utf-8"))).decode("utf-8")
      
    return retval
