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
import os
import sys

# Update PYTHONPATH to include Provisioner API installed at:
# /usr/local/lib/python3.6/site-packages/cortx-prvsnr-*
sys.path.append(os.path.join(
       'usr', 'local', 'lib', 'python3.6', 'site-packages'))

import provisioner
from provisioner.utils import run_subprocess_cmd

logger = logging.getLogger(__name__)


def decrypt(component, secret):
    """Decrypt secret.

    Args:
      secret: Secret to be decrypted.
    """
    from cortx.utils.security.cipher import Cipher

    retval = None
    cluster_id = getattr(sys.modules[__name__], '__grains__')['cluster_id']
    cipher_key = Cipher.generate_key(cluster_id, component)

    if secret:
        retval = (Cipher.decrypt(cipher_key, secret.encode("utf-8"))).decode("utf-8")

    return retval


def validate_firewall():  # noqa: C901
    """Validates firewall ports from pillar data.

    Args:
      Takes no mandatory argument as input.

    """
    validate = False
    ret_code = False
    _target_node = getattr(sys.modules[__name__], '__grains__')['id']
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

    # TODO: Future scope: as utilities increase in Salt,
    # opt for wrapper around run_subprocess_cmd and
    # use it in salt utility modules as srv/_utils/<file>.py
    # Ref: https://github.com/Seagate/cortx-prvsnr/pull/1111#discussion_r614055880

    for port, service in zip(validate_ports, validate_services):

        tcp_port = run_subprocess_cmd([f"ss -ltrp | grep {port}"],
                                     check=False, shell=True).stdout  # nosec
        tcp_svc = run_subprocess_cmd([f"ss -lt | grep {service}"],
                                     check=False, shell=True).stdout  # nosec

        udp_port = run_subprocess_cmd([f"ss -lurp | grep {port}"],
                                     check=False, shell=True).stdout  # nosec
        udp_svc = run_subprocess_cmd([f"ss -lu | grep {service}"],
                                     check=False, shell=True).stdout  # nosec

        # Either of TCP/ UDP port and service should pass
        if not (
            (tcp_port or udp_port) and
            (tcp_svc or udp_svc)
        ):
            ret_code = True

    if ret_code:
        logger.error(
            "Failed: Validation of open firewall ports. Ensure all services "
            "and ports mentioned in pillar are running and accessible."
        )
    else:
        validate = True
        logger.info("Success: Validation of open firewall ports")

    return validate
