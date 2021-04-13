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
# salt-call lyveutils.decrypt "component" "secret"

import logging
import provisioner
from salt import client

logger = logging.getLogger(__name__)


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

#TODO: verify command - most likely to return False always

def validate_firewall():
    """ Validates open ports

    Validates ports from pillar firewall data.
    Args: Takes no mandatory argument as input.

    """
    _target_node = __grains__['id']
    data = provisioner.pillar_get()
    fw_pillar = data[_target_node]["firewall"]
    validate_ports = []
    validate_services = []

    for zone in fw_pillar:
        for services, ports in fw_pillar[zone]["ports"].items():
            validate_services.append(services)
            for pt in ports:
                port_num = int(''.join(filter(str.isdigit, pt)))
                validate_ports.append(port_num)

    for port, service in zip(validate_ports, validate_services):
        tcp_port = __utils__['process.simple_process'](f"netstat -ltp | grep {port}")
        tcp_svc = __utils__['process.simple_process'](f"netstat -lt | grep {service}")

        udp_port = __utils__['process.simple_process'](f"netstat -lup | grep {port}")
        udp_svc = __utils__['process.simple_process'](f"netstat -lu | grep {service}")

    if (tcp_port or udp_port) and (tcp_svc or udp_svc):
        logger.info("Success: Validation of open firewall ports")

        return True
    else:
        logger.error("Error in validating open firewall ports")

        return False
