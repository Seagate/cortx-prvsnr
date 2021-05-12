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

# Standard packages
import logging
import os
import sys

from provisioner.config import (
    PRVSNR_USER_FILEROOT_DIR,
    ALL_MINIONS
)

from provisioner.salt import (
    cmd_run
)

from provisioner.utils import run_subprocess_cmd

# /usr/local/lib/python3.6/site-packages/cortx-prvsnr-*
sys.path.append(os.path.join(
    'usr', 'local', 'lib', 'python3.6', 'site-packages'))

# Cortx packages

logger = logging.getLogger(__name__)

PRVSNR_USER_TLS_CERT_DIR = 'components/csm/files/tls/'
DEST = '/var/csm/tls'


def generate_csm_tls():
    csm_user = __pillar__['cortx']['software']['csm']['user']
    tls_root_dir = PRVSNR_USER_FILEROOT_DIR / PRVSNR_USER_TLS_CERT_DIR

    cmd_run(
        f"install -d -m 0700 -o {csm_user} -g {csm_user} {DEST}",
        targets=ALL_MINIONS)

    # generate native cert and native key

    cmd = "umask 0177 && openssl req -x509 -newkey rsa:4096 " \
        f"-keyout {DEST}/native.key -nodes " \
        f"-out {DEST}/native.crt -days 365 -subj '/C=/ST=/L=/O=/OU=/CN=/' "

    run_subprocess_cmd([cmd], check=False, shell=True)

    # this block is to be removed after csm validation checks are updated for certs
    # start
    # generate domain cert and domain key
    cmd = "umask 0177 && openssl req -x509 -newkey rsa:4096 " \
        f"-keyout {DEST}/domain.key -nodes " \
        f"-out {DEST}/domain.crt -days 365 -subj '/C=/ST=/L=/O=/OU=/CN=/' "

    run_subprocess_cmd([cmd], check=False, shell=True)
    # end

    logger.info("Copying tls certs to provisioner file_roots")

    __salt__['file.mkdir'](tls_root_dir)
    __salt__['file.copy'](
        DEST,
        tls_root_dir,
        recurse=True,
        remove_existing=True)

    return True
