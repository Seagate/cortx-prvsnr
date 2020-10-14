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
from enum import Enum
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
PRVSNR_CLI_DIR = PRVSNR_ROOT_DIR / 'cli'

PRVSNR_DATA_ROOT_DIR = Path('/var/lib/seagate/cortx/provisioner')
PRVSNR_DATA_SHARED_DIR = Path('/var/lib/seagate/cortx/provisioner/shared')
PRVSNR_DATA_LOCAL_DIR = Path('/var/lib/seagate/cortx/provisioner/local')

PRVSNR_USER_SALT_DIR = PRVSNR_DATA_SHARED_DIR / 'srv'
# PRVSNR_USER_LOCAL_SALT_DIR = PRVSNR_DATA_LOCAL_DIR / 'srv'
PRVSNR_FACTORY_PROFILE_DIR = PRVSNR_DATA_SHARED_DIR / 'factory_profile'

# reflects salt-master file_roots configuration
PRVSNR_USER_FILEROOT_DIR = PRVSNR_USER_SALT_DIR / 'salt'
# PRVSNR_USER_LOCAL_FILEROOT_DIR = PRVSNR_USER_LOCAL_SALT_DIR / 'salt'
# reflects pillar/top.sls
PRVSNR_USER_PILLAR_DIR = PRVSNR_USER_SALT_DIR / 'pillar'
# PRVSNR_USER_LOCAL_PILLAR_DIR = PRVSNR_USER_LOCAL_SALT_DIR / 'pillar'

PRVSNR_PILLAR_CONFIG_INI = str(
    PRVSNR_FACTORY_PROFILE_DIR / 'srv/salt/provisioner/files/minions/all/config.ini'  # noqa: E501
)

# TODO EOS-12076 EOS-12334

CORTX_SINGLE_ISO_DIR = 'cortx_single_iso'
CORTX_ISO_DIR = 'cortx_iso'
CORTX_3RD_PARTY_ISO_DIR = '3rd_party'

PRVSNR_CORTX_REPOS_BASE_DIR = (
    PRVSNR_DATA_LOCAL_DIR / 'cortx_repos'
)
PRVSNR_CORTX_SINGLE_ISO = (
    PRVSNR_CORTX_REPOS_BASE_DIR / f'{CORTX_SINGLE_ISO_DIR}.iso'
)
PRVSNR_CORTX_ISO = (
    PRVSNR_CORTX_REPOS_BASE_DIR / f'{CORTX_ISO_DIR}.iso'
)
PRVSNR_CORTX_DEPS_ISO = (
    PRVSNR_CORTX_REPOS_BASE_DIR / f'{CORTX_3RD_PARTY_ISO_DIR}.iso'
)


# FIXME EOS-12334 should be inside factory installation directory
#    relative paths
PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR = Path('misc_pkgs/swupdate/repo/files')
PRVSNR_USER_FILES_SSL_CERTS_FILE = Path(
    'components/misc_pkgs/ssl_certs/files/stx.pem'
)
SSL_CERTS_FILE = Path('/etc/ssl/stx/stx.pem')

# pillar structures
PRVSNR_DEF_PILLAR_HOST_DIR_TMPL = str(
    PRVSNR_PILLAR_DIR / 'minions/{minion_id}'
)

PRVSNR_USER_PILLAR_PREFIX = 'uu_'
PRVSNR_USER_PILLAR_ALL_HOSTS_DIR = PRVSNR_USER_PILLAR_DIR / 'groups/all'
PRVSNR_USER_PILLAR_HOST_DIR_TMPL = str(
    PRVSNR_USER_PILLAR_DIR / 'minions/{minion_id}'
)

# PRVSNR_USER_LOCAL_PILLAR_ALL_HOSTS_DIR = (
#    PRVSNR_USER_LOCAL_PILLAR_DIR / 'groups/all'
# )
# PRVSNR_USER_LOCAL_PILLAR_HOST_DIR_TMPL = str(
#    PRVSNR_USER_LOCAL_PILLAR_DIR / 'minions/{minion_id}'
# )


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
LOG_RSYSLOG_HANDLER = 'rsyslog'
LOG_CMD_FILTER = 'cmd_filter'

LOG_HUMAN_FORMATTER = 'human'
LOG_FULL_FORMATTER = 'full'
#   logfile habdler for the following commands
#   will be enabled forcibly
#   TODO move to some parent type instead
LOG_FORCED_LOGFILE_CMDS = [
    'set_network',
    'set_swupdate_repo',
    'sw_update',
    'fw_update',
    'set_ssl_certs',
    'reboot_server',
    'reboot_controller',
    'shutdown_controller',
    'configure_cortx',
    'create_user',
    'cmd_run',
    # deploy commands might be run separately on a primary host
    'deploy',
    'deploy_vm',
    'deploy_jbod',
    'deploy_dual',
    'replace_node'
]

LOG_TRUNC_MSG_TMPL = "<TRUNCATED> {} ..."
LOG_TRUNC_MSG_SIZE_MAX = 4096 - len(LOG_TRUNC_MSG_TMPL)

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


def profile_base_dir(
    location: Union[str, Path] = None,
    setup_name: Optional[str] = 'default'
):
    if location is None:
        location = Path.cwd() / PROFILE_DIR_NAME
    else:
        location = location.resolve()

    return (location / setup_name)


def profile_paths(base_dir: Optional[Path] = None) -> Dict:
    if base_dir is None:
        base_dir = profile_base_dir()

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


# TODO IMPROVE EOS-8473 better name
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
# CORTX_REPOS_BASE_URL = 'http://cortx-storage.colo.seagate.com/releases/cortx'

LOCALHOST_IP = '127.0.0.1'
LOCALHOST_DOMAIN = 'localhost'


class DistrType(Enum):
    """Distribution types"""
    CORTX = "cortx"       # only release packages
    BUNDLE = "bundle"     # release packages along with all dependencies


# Defines a "frozen" list for allowed commands and supported by provisioner
# API for remote execution
SUPPORTED_REMOTE_COMMANDS = frozenset({'cortxcli'})

OTHER_STORAGE_TYPE = "Other"


class ServerType(Enum):
    """Class-enumeration which represents possible server types"""

    VIRTUAL = "virtual"
    PHYSICAL = "physical"


# Constant block for setup info fields
NODES = "nodes"
SERVERS_PER_NODE = "servers_per_node"
STORAGE_TYPE = "storage_type"
SERVER_TYPE = "server_type"

SETUP_INFO_FIELDS = (NODES, SERVERS_PER_NODE, STORAGE_TYPE, SERVER_TYPE)

# TODO: EOS-12418-improvement: maybe, it makes sense to move it to values.py
NOT_AVAILABLE = "N/A"
