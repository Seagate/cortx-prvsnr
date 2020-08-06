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

from pathlib import Path
from typing import Union, Dict, Optional

CONFIG_MODULE_DIR = Path(__file__).resolve().parent

# Note. might be incorrect in case package installation

try:
    PROJECT_PATH = CONFIG_MODULE_DIR.parents[2]
except IndexError:
    PROJECT_PATH = None
else:
    # TODO IMPROVE more accurate way for that
    for path in ('srv', 'pillar', 'files'):
        if not (PROJECT_PATH / path).is_dir():
            PROJECT_PATH = None
            break

# TODO
#  - rename to defaults.py or constants.py or ...
#  - then rename base.py to config.py
#  - remove PRVSNR_ prefix

PRVSNR_ROOT_DIR = Path('/opt/seagate/cortx/provisioner')
PRVSNR_FILEROOT_DIR = PRVSNR_ROOT_DIR / 'srv'
PRVSNR_PILLAR_DIR = PRVSNR_ROOT_DIR / 'pillar'

PRVSNR_DATA_ROOT_DIR = Path('/var/lib/seagate/cortx/provisioner')
PRVSNR_DATA_SHARED_DIR = Path('/var/lib/seagate/cortx/provisioner/shared')

PRVSNR_FACTORY_PROFILE_DIR = PRVSNR_DATA_SHARED_DIR / 'factory_profile'
PRVSNR_USER_SALT_DIR = PRVSNR_DATA_SHARED_DIR / 'srv'
# reflects master file_roots configuration
PRVSNR_USER_FILEROOT_DIR = PRVSNR_USER_SALT_DIR / 'salt'
# reflects pillar/top.sls
PRVSNR_USER_PILLAR_DIR = PRVSNR_USER_SALT_DIR / 'pillar'

#    relative paths
PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR = Path('misc_pkgs/swupdate/repo/files')
PRVSNR_USER_FILES_SSL_CERTS_FILE = Path(
    'components/misc_pkgs/ssl_certs/files/stx.pem'
)
SSL_CERTS_FILE = Path('/etc/ssl/stx/stx.pem')

PRVSNR_USER_PI_ALL_HOSTS_DIR = PRVSNR_USER_PILLAR_DIR / 'groups/all'
PRVSNR_DEF_PI_HOST_DIR_TMPL = str(
    PRVSNR_PILLAR_DIR / 'minions/{minion_id}'
)
PRVSNR_USER_PI_HOST_DIR_TMPL = str(
    PRVSNR_USER_PILLAR_DIR / 'minions/{minion_id}'
)

SEAGATE_USER_HOME_DIR = Path('/opt/seagate/users')
SEAGATE_USER_FILEROOT_DIR_TMPL = str(
    'components/provisioner/files/users/{uname}'
)

ALL_MINIONS = '*'
LOCAL_MINION = '__local__'

PRVSNR_VALUES_PREFIX = 'PRVSNR_'

# TODO ??? make that dynamic (based on pillar structure)
PRVSNR_CORTX_COMPONENTS = [
    'cluster',
    'commons',
    'controller',
    'corosync-pacemaker',
    'elasticsearch',
    'motr',
    'haproxy',
    'keepalived',
    'openldap',
    'rabbitmq',
    'release',
    'rsyslog',
    's3clients',
    's3server',
    'sspl',
    'storage_enclosure',
    'system',
    'uds'
]

CONTROLLER_A = 'a'
CONTROLLER_B = 'b'
CONTROLLER_BOTH = 'both'

PRVSNRUSERS_GROUP = 'prvsnrusers'

PRVSNR_CLI_MACHINE_OUTPUT = ('json', 'yaml')
PRVSNR_CLI_OUTPUT = tuple(list(PRVSNR_CLI_MACHINE_OUTPUT) + ['plain'])
PRVSNR_CLI_OUTPUT_DEFAULT = 'plain'

PRVSNR_CONFIG_FILE = 'provisioner.conf'

# logging
PRVSNR_LOG_ROOT_DIR = Path('/var/log/seagate/provisioner')
LOG_ROOT_DIR = (
    PRVSNR_LOG_ROOT_DIR
    if PRVSNR_LOG_ROOT_DIR.exists()
    else Path('.').resolve()
)

LOG_NULL_HANDLER = '_null'
LOG_CONSOLE_HANDLER = 'console'
LOG_FILE_HANDLER = 'logfile'
LOG_CMD_FILTER = 'cmd_filter'

LOG_HUMAN_FORMATTER = 'human'
LOG_FULL_FORMATTER = 'full'
#   logfile habdler for the following commands
#   will be enabled forcibly
LOG_FORCED_LOGFILE_CMDS = [
    'set_network',
    'set_swupdate_repo',
    'sw_update',
    'fw_update',
    'set_ssl_certs',
    'reboot_server',
    'reboot_controller',
    'shutdown_controller',
    'create_user',
    'replace_node'
]

# bundled salt roots dirs
BUNDLED_SALT_DIR = CONFIG_MODULE_DIR / 'srv'
BUNDLED_SALT_FILEROOT_DIR = BUNDLED_SALT_DIR / 'salt'
BUNDLED_SALT_PILLAR_DIR = BUNDLED_SALT_DIR / 'pillar'

# profile parameters
# TODO IMPROVE consider to have home dir as option for profile location
# TODO IMPROVE consider to make that configurable (e.g. env variable)

PROFILE_DIR_NAME = '.provisioner'
PRVSNR_USER_FACTORY_PROFILE_DIR = (
    Path.home() / PROFILE_DIR_NAME / 'factory_profile'
)


def profile_paths(
    location: Union[str, Path] = None,
    setup_name: Optional[str] = 'default'
) -> Dict:

    if location is None:
        location = Path.cwd() / PROFILE_DIR_NAME
    else:
        location = location.resolve()

    base_dir = location / setup_name
    ssh_dir = base_dir / '.ssh'
    salt_dir = base_dir / 'srv'
    salt_fileroot_dir = salt_dir / 'salt'
    salt_pillar_dir = salt_dir / 'pillar'
    salt_cache_dir = salt_dir / 'cachedir'
    salt_pki_dir = salt_dir / 'pki_dir'
    salt_config_dir = salt_dir / 'config'

    salt_factory_fileroot_dir = base_dir / 'srv_factory'
    salt_factory_profile_dir = salt_factory_fileroot_dir / 'profile'

    setup_key_file = ssh_dir / 'setup.id_rsa'
    setup_key_pub_file = ssh_dir / 'setup.id_rsa.pub'
    salt_master_file = salt_config_dir / 'master'
    salt_minion_file = salt_config_dir / 'minion'
    salt_salt_file = salt_config_dir / 'Saltfile'
    salt_roster_file = salt_config_dir / 'roster'
    salt_ssh_log_file = salt_config_dir / 'salt_ssh.log'
    salt_call_log_file = salt_config_dir / 'salt_call.log'

    return {
        'base_dir': base_dir,
        'ssh_dir': ssh_dir,
        'salt_dir': salt_dir,
        'salt_fileroot_dir': salt_fileroot_dir,
        'salt_pillar_dir': salt_pillar_dir,
        'salt_cache_dir': salt_cache_dir,
        'salt_pki_dir': salt_pki_dir,
        'salt_config_dir': salt_config_dir,

        'salt_factory_fileroot_dir': salt_factory_fileroot_dir,
        'salt_factory_profile_dir': salt_factory_profile_dir,

        'setup_key_file': setup_key_file,
        'setup_key_pub_file': setup_key_pub_file,
        'salt_master_file': salt_master_file,
        'salt_minion_file': salt_minion_file,
        'salt_salt_file': salt_salt_file,
        'salt_roster_file': salt_roster_file,
        'salt_ssh_log_file': salt_ssh_log_file,
        'salt_call_log_file': salt_call_log_file
    }


# TODO IMPROVE CORTX-8473 better name
REPO_BUILD_DIRS = [
    '.build',
    'build',
    '.boxes',
    '.eggs',
    '.vdisks',
    '.vagrant',
    '.pytest_cache',
    f'{PROFILE_DIR_NAME}',
    '__pycache__',
    'packer_cache',
    'tmp'
]

# Using any base path is risky as it builds a dependency inside code.
# This results in loss of flexibility.
# CORTX_REPOS_BASE_URL = 'http://cortx-storage.colo.seagate.com/releases/eos'

LOCALHOST_IP = '127.0.0.1'
LOCALHOST_DOMAIN = 'localhost'
