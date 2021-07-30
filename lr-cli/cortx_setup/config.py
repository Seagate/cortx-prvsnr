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

from pathlib import Path

ALL_MINIONS = '*'

CONFSTORE_CLUSTER_FILE = Path(
    '/opt/seagate/cortx_configs/provisioner_cluster.json'
)
PRVSNR_PILLAR_DIR = Path(
    '/opt/seagate/cortx/provisioner/pillar'
)
PRVSNR_LOG_DIR= Path(
    '/var/log/seagate/provisioner'
)

local_pillars = ['cluster', 'storage', 'system', 'firewall']

# Will be changed to confstore yaml path
CONFIG_PATH = Path('/root/config.ini')

ENCLOSURE_ID = Path('/etc/enclosure-id')
CERT_PATH = Path('/etc/ssl/stx')

# resource map generation and manifest generation
RETRIES = 30
WAIT = 30
HEALTH_PATH = 'provisioner/common_config/resource_map_path'
MANIFEST_PATH = 'provisioner/common_config/manifest_path'

HW_TYPE = 'HW'
VM_TYPE = 'VM'
SOURCE_PATH = PRVSNR_PILLAR_DIR / 'components' / 'storage.sls'
DEST_PATH = PRVSNR_PILLAR_DIR / 'samples' / 'storage.sls'

BMC_COMPONENT = 'server_node'

# Support user
SUPPORT_USER_NAME = 'support'
SUPPORT_CRON_TIME = 24                       # time in hours
SUPPORT_CRON_SCRIPT = 'sudo /opt/seagate/cortx/provisioner/srv/components/provisioner/scripts/support --set-credentials'
