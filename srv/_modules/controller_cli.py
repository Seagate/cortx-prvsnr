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
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules
# $ salt-call controller_cli.fetch_enclosure_serial
# On successfull run, the fetched enclosure id/serial is kept at:
# /etc/enclosure-id file.

# Standard packages
import logging
import os
import sys

# Update PYTHONPATH to include Provisioner API installed at:
# /usr/local/lib/python3.6/site-packages/cortx-prvsnr-*
sys.path.append(os.path.join(
       'usr', 'local', 'lib', 'python3.6', 'site-packages'))

# Cortx packages
from provisioner.utils import run_subprocess_cmd

from pathlib import Path
logger = logging.getLogger(__name__)


def fetch_enclosure_serial():

    current_node = __grains__['id']

    current_enclosure = "enclosure-" + ((current_node).split('-'))[1]
    ctrl_cli_utility = __pillar__['provisioner']['storage']['controller']['cli_utility_path']

    host = __pillar__['storage'][current_enclosure ]['controller']['primary']['ip']
    user = __pillar__['storage'][current_enclosure]['controller']['user']
    secret = __pillar__['storage'][current_enclosure]['controller']['secret']
    logs = "/var/log/seagate/provisioner/controller-cli.log"
    _opt = "--show-license"

    logger.info("[ INFO ] Running controller-cli utility to get enclosure serial...")
    _cmd = (f"sh {ctrl_cli_utility} host -h {host} -u {user} -p '{secret}' {_opt}"
           " | grep -A2 Serial | tail -1 > /etc/enclosure-id")
    run_subprocess_cmd([_cmd], check=False, shell=True).stdout.splitlines()

    _enc_id_file = Path('/etc/enclosure-id')
    if not _enc_id_file.exists():
        msg = ("ERROR: Could not generate the enclosure id "
              "from controller cli utility, please check "
              f"the {str(logs)} for more details")
        # raise Exception(msg)
        logger.error(msg)
        return False
    else:
        # Check if file /etc/enclosure-id has correct content:
        # 1. has only one line and
        # 2. has only one word - enclosure serial.
        with open(_enc_id_file) as _fp:
            _line_cnt = 0
            _words = 0
            for _line in _fp:
                logger.info(f"content of line {_line_cnt}: {_line}")
                _words = _line.strip()
                _line_cnt += 1

        _n_words = 1
        for i in _words:
            if i == " ":
                _n_words += 1

        if ((_line_cnt > 1) or (_n_words > 1)):
            msg = "ERROR: The contents of /etc/enclosure-id looks incorrect, failing"
            logger.error(msg)
            return False

    logger.info("Enclosure id generated successfully and is kept at /etc/enclosure-id")

    return True
