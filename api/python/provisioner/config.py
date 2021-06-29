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
import os
import itertools
from typing import Union, Dict, Optional

CONFIG_MODULE_DIR = Path(__file__).resolve().parent

# Note. might be incorrect in case package installation

PROJECT_PATH = os.getenv('PROJECT_PATH')

if not PROJECT_PATH:
    try:
        PROJECT_PATH = CONFIG_MODULE_DIR.parents[2]
    except IndexError:
        PROJECT_PATH = None
else:
    PROJECT_PATH = Path(PROJECT_PATH).resolve()

# TODO IMPROVE more accurate way for that
for path in ('srv', 'pillar', 'files'):
    if not (PROJECT_PATH / path).is_dir():
        PROJECT_PATH = None
        break

API_SPEC_PATH = CONFIG_MODULE_DIR / 'api_spec.yaml'
PARAMS_SPEC_PATH = CONFIG_MODULE_DIR / 'params_spec.yaml'
CLI_SPEC_PATH = CONFIG_MODULE_DIR / 'cli_spec.yaml'
ATTRS_SPEC_PATH = CONFIG_MODULE_DIR / 'attrs_spec.yaml'

API_SPEC_PATH = CONFIG_MODULE_DIR / 'api_spec.yaml'
PARAMS_SPEC_PATH = CONFIG_MODULE_DIR / 'params_spec.yaml'
CLI_SPEC_PATH = CONFIG_MODULE_DIR / 'cli_spec.yaml'
ATTRS_SPEC_PATH = CONFIG_MODULE_DIR / 'attrs_spec.yaml'

# TODO
#  - rename to defaults.py or constants.py or ...
#  - then rename base.py to config.py
#  - remove PRVSNR_ prefix

CLUSTER_ID_FILE = Path('/etc/cluster-id')

CORTX_CONFIG_DIR = Path('/opt/seagate/cortx_configs')
CORTX_ROOT_DIR = Path('/opt/seagate/cortx')
PRVSNR_TMP_DIR = Path(Path.home() / '.tmp/seagate/prvsnr/')
CONFSTORE_CLUSTER_CONFIG = CORTX_CONFIG_DIR / 'provisioner_cluster.json'
CONFSTORE_ROOT_FILE = Path('components/system/files/provisioner_cluster.json')

PRVSNR_ROOT_DIR = Path('/opt/seagate/cortx/provisioner')
PRVSNR_FILEROOT_DIR = PRVSNR_ROOT_DIR / 'srv'
PRVSNR_PILLAR_DIR = PRVSNR_ROOT_DIR / 'pillar'
PRVSNR_CLI_DIR = PRVSNR_ROOT_DIR / 'cli'

PRVSNR_DATA_ROOT_DIR = Path('/var/lib/seagate/cortx/provisioner')
PRVSNR_DATA_SHARED_DIR = Path('/var/lib/seagate/cortx/provisioner/shared')
PRVSNR_DATA_LOCAL_DIR = Path('/var/lib/seagate/cortx/provisioner/local')

PRVSNR_USER_SALT_DIR = PRVSNR_DATA_SHARED_DIR / 'srv'
PRVSNR_USER_LOCAL_SALT_DIR = PRVSNR_DATA_LOCAL_DIR / 'srv'
PRVSNR_FACTORY_PROFILE_DIR = PRVSNR_DATA_SHARED_DIR / 'factory_profile'
PRVSNR_LOCKS_FILES_DIR = PRVSNR_DATA_SHARED_DIR / 'locks'

# reflects salt-master file_roots configuration
PRVSNR_USER_FILEROOT_DIR = PRVSNR_USER_SALT_DIR / 'salt'
PRVSNR_USER_LOCAL_FILEROOT_DIR = PRVSNR_USER_LOCAL_SALT_DIR / 'salt'
# reflects pillar/top.sls
PRVSNR_USER_PILLAR_DIR = PRVSNR_USER_SALT_DIR / 'pillar'
PRVSNR_USER_LOCAL_PILLAR_DIR = PRVSNR_USER_LOCAL_SALT_DIR / 'pillar'


SALT_JOBS_CACHE_DIR = Path('/var/cache/salt/master/jobs')

# Notes:
# 1. how salt's pillar roots organized:
#   - salt searches for files in each root
#   - if a file (with the same path, path is relative to pillar root)
#     has been found in one of the previous roots - it is ignored
#   - all found files are sorted alphabetically
#   - then merge logic happens: later files win
#     (e.g. file zzz.sls wins aaa.sls)
# 2. why we nee prefixes:
#   - we don't want the same pillar file paths in different roots
#   - we need them to be sorted according to priorities we have in
#     salt master/minion config files
#     (e.g. default ones have less priority than user ones,
#           shared user pillar has less priority than local one)
PRVSNR_FACTORY_PILLAR_PREFIX = "u_factory_"
PRVSNR_USER_PILLAR_PREFIX = 'uu_'
PRVSNR_USER_LOCAL_PILLAR_PREFIX = 'zzz_'

PRVSNR_PILLAR_CONFIG_INI = str(
    PRVSNR_FACTORY_PROFILE_DIR / 'srv/salt/provisioner/files/minions/all/config.ini'  # noqa: E501
)


REPO_CANDIDATE_NAME = 'candidate'
RELEASE_FACTORY_INFO_FILE = 'RELEASE_FACTORY.INFO'
RELEASE_INFO_FILE = 'RELEASE.INFO'
THIRD_PARTY_RELEASE_INFO_FILE = 'THIRD_PARTY_RELEASE.INFO'
CORTX_RELEASE_INFO_FILE = 'CORTX_RELEASE.INFO'

CORTX_RELEASE_FACTORY_INFO_PATH = (
    Path('/etc/yum.repos.d/') / RELEASE_FACTORY_INFO_FILE
)
CORTX_RELEASE_INFO_PATH = CORTX_ROOT_DIR / RELEASE_INFO_FILE

SALT_MASTER_CONFIG_DEFAULT = '/etc/salt/master'
SALT_MINION_CONFIG_DEFAULT = '/etc/salt/minion'
SALT_ROSTER_DEFAULT = '/etc/salt/roster'

# TODO EOS-12076 EOS-12334

CORTX_SINGLE_ISO_DIR = 'cortx_single_iso'
OS_ISO_DIR = 'os'
CORTX_ISO_DIR = 'cortx_iso'
CORTX_3RD_PARTY_ISO_DIR = '3rd_party'
CORTX_PYTHON_ISO_DIR = 'python_deps'


class ISOVersion(Enum):

    """Simple class enumeration that defines different ISO bundle
    scheme versions.
    """

    VERSION1 = "1.0.0"
    VERSION2 = "2.0.0"


class ISOKeywordsVer2:

    """Directory names, file names and other important keywords for ISO
    structure of version 2.

    This class is used for simple grouping of common names for ISO structure
    of version 2. It should help to avoid hard cording such names directly in
    code.

    """

    FW = "fw"
    SERVER = "server"
    STORAGE = "storage"
    OS = "os"
    PATCHES = "patches"
    SW = "sw"
    CORTX = "cortx"
    EXTERNAL = "external"
    PYTHON = "python"
    RPM = "rpm"
    EPEL_7 = "EPEL-7"
    COMMONS = "commons"
    PERFORMANCE = "performance"


class UpgradeReposVer2(Enum):

    """Names of upgrade repositories from SW upgrade ISO bundle of version 2"""

    CORTX = ISOKeywordsVer2.CORTX
    EPEL_7 = ISOKeywordsVer2.EPEL_7
    COMMONS = ISOKeywordsVer2.COMMONS
    PERFORMANCE = ISOKeywordsVer2.PERFORMANCE


PRVSNR_CORTX_REPOS_BASE_DIR = (
    PRVSNR_DATA_LOCAL_DIR / 'cortx_repos'
)
PRVSNR_OS_ISO = (
    PRVSNR_CORTX_REPOS_BASE_DIR / f'{OS_ISO_DIR}.iso'
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
PRVSNR_USER_FILES_SWUPGRADE_REPOS_DIR = Path('repos/files')
PRVSNR_USER_FILES_SSL_CERTS_FILE = Path(
    'components/misc_pkgs/ssl_certs/files/stx.pem'
)
SSL_CERTS_FILE = Path('/etc/ssl/stx/stx.pem')

GLUSTERFS_VOLUME_SALT_JOBS = Path('/srv/glusterfs/volume_salt_cache_jobs')
GLUSTERFS_VOLUME_NAME_SALT_JOBS = 'volume_salt_cache_jobs'
GLUSTERFS_VOLUME_PRVSNR_DATA = Path('/srv/glusterfs/volume_prvsnr_data')
GLUSTERFS_VOLUME_NAME_PRVSNR_DATA = 'volume_prvsnr_data'

GLUSTERFS_VOLUME_FILEROOT_DIR = GLUSTERFS_VOLUME_PRVSNR_DATA / 'srv/salt'
GLUSTERFS_VOLUME_PILLAR_DIR = GLUSTERFS_VOLUME_PRVSNR_DATA / 'srv/pillar'

SEAGATE_USER_HOME_DIR = Path('/opt/seagate/users')
SEAGATE_USER_FILEROOT_DIR_TMPL = str(
    'components/provisioner/files/users/{uname}'
)

SSH_PRIV_KEY = Path('/root/.ssh/id_rsa_prvsnr')
SSH_PUB_KEY = Path('/root/.ssh/id_rsa_prvsnr.pub')

ALL_MINIONS = '*'
ALL_TARGETS = ALL_MINIONS  # XXX rethink later
LOCAL_MINION = '__local__'
# NOTE: used mostly by provisioner Lock files since '*' can not be used as a
# part of file name
ALL_TARGETS_ALIAS = 'all'

PRVSNR_VALUES_PREFIX = 'PRVSNR_'
CLI_SPEC_PY_OBJS_PREFIX = '__py__:'

SECRET_MASK = '*' * 7

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
    'release',
    'rsyslog',
    's3clients',
    's3server',
    'sspl',
    'storage',
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
PIP_CONFIG_FILE = '/etc/pip.conf'

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
LOG_FILE_SALT_HANDLER = 'saltlogfile'
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


# List of commands for which we purposely reduce log level severity to suppress
# logging noise and prevent log files size growing.
LOG_SUPPRESSION_CMDS = [
    'get_params',
    "get_result",
    "grains_get",
    "pillar_get",
    "get_params",
    "get_cluster_id",
    "get_node_id",
    "get_release_version",
    "get_factory_version",
    "get_setup_info"
]


LOG_TRUNC_MSG_TMPL = "<TRUNCATED> {} ..."
LOG_TRUNC_MSG_SIZE_MAX = 4096 - len(LOG_TRUNC_MSG_TMPL)


class LogLevelTypes(Enum):

    RSYSLOG = f"{LOG_RSYSLOG_HANDLER}_level"
    CONSOLE = f"{LOG_CONSOLE_HANDLER}_level"
    LOGFILE = f"{LOG_FILE_HANDLER}_level"


# bundled salt roots dirs
BUNDLED_SALT_DIR = CONFIG_MODULE_DIR / 'srv'
BUNDLED_SALT_FILEROOT_DIR = BUNDLED_SALT_DIR / 'salt'
BUNDLED_SALT_FILEROOT_VENDOR_DIR = BUNDLED_SALT_DIR / 'salt-vendor'
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
    setup_name: Optional[str] = 'default',
    profile: Optional[Union[str, Path]] = None
):
    if profile:
        return Path(profile).resolve()
    if location is None:
        location = Path.home() / PROFILE_DIR_NAME
    else:
        location = Path(location)
        location = location.resolve()

    return location / setup_name


# TODO make a class
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
    salt_bootstrap_roster_file = salt_config_dir / 'roster_bootstrap'
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
        'salt_bootstrap_roster_file': salt_bootstrap_roster_file,
        'salt_ssh_log_file': salt_ssh_log_file,
        'salt_call_log_file': salt_call_log_file
    }


REPO_VERSION_RAW = '__raw__'  # to not interfere with any reasonable git refs


LOCALHOST_IP = '127.0.0.1'
LOCALHOST_DOMAIN = 'localhost'


# TODO rename to DistType
class DistrType(Enum):
    """Distribution types"""
    # only release packages, optional separate os and deps
    CORTX = "cortx"
    # release packages along with all dependencies,
    # optional python index inside,
    # optional separate os
    BUNDLE = "bundle"


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
STORAGE_SETS = "1"
SERVERS_PER_NODE = "servers_per_node"
STORAGE_TYPE = "storage_type"
SERVER_TYPE = "server_type"

SETUP_INFO_FIELDS = (NODES, SERVERS_PER_NODE, STORAGE_TYPE, SERVER_TYPE)

# TODO: EOS-12418-improvement: maybe, it makes sense to move it to values.py
NOT_AVAILABLE = "N/A"

CLI_NEW_SERVICE_USER_PWD_VALUE = '__GENERATE__'  # nosec


class Checks(Enum):

    """ Enumeration for available checks/validations """

    NETWORK = "network"
    CONNECTIVITY = "connectivity"
    BMC_ACCESSIBILITY = "bmc_accessibility"
    BMC_STONITH = "bmc_stonith"
    COMMUNICABILITY = "communicability"
    CLUSTER_STATUS = "cluster_status"
    LOGS_ARE_GOOD = "logs_are_good"
    PASSWORDLESS_SSH_ACCESS = "passwordless_ssh_access"
    STORAGE_LVMS = "storage_lvms"
    STORAGE_LUNS = "storage_luns"
    LUNS_MAPPED = "luns_mapped"
    MGMT_VIP = "mgmt_vip"
    HOSTNAMES = "hostnames"
    PUB_DATA_IP = "public_data_ip"
    CONTROLLER_IP = "controller_ip"
    STORAGE_HBA = "storage_hba"
    NETWORK_DRIVERS = "network_drivers"
    NETWORK_HCA = "network_hca"
    UPGRADE_ISO_VERSION = "upgrade_iso_version"
    ACTIVE_UPGRADE_ISO = "active_upgrade_iso"


class GroupChecks(Enum):

    """ Enum for group checks. """

    ALL = "all"
    DEPLOY_PRE_CHECKS = "deploy_pre_checks"
    DEPLOY_POST_CHECKS = "deploy_post_checks"
    REPLACENODE_CHECKS = "replacenode_checks"
    SWUPDATE_CHECKS = "swupdate_checks"
    SWUPGRADE_CHECKS = "swupgrade_checks"
    UNBOXING_PRE_CHECKS = "unboxing_pre_checks"
    UNBOXING_POST_CHECKS = "unboxing_post_checks"


# Set of supported validations/checks
CHECKS = [check.value for check in Checks]

GROUP_CHECKS = [check.value for check in GroupChecks]

DEPLOY_PRE_CHECKS = {
    Checks.NETWORK_DRIVERS.value,
    Checks.NETWORK_HCA.value,
    Checks.STORAGE_HBA.value,
    Checks.STORAGE_LUNS.value
}

SWUPDATE_CHECKS = {
    Checks.NETWORK.value,
    Checks.CONNECTIVITY.value,
    Checks.BMC_ACCESSIBILITY.value,
    Checks.COMMUNICABILITY.value,
    Checks.CLUSTER_STATUS.value,
    Checks.LOGS_ARE_GOOD.value,
    Checks.PASSWORDLESS_SSH_ACCESS.value
}

SWUPGRADE_CHECKS = (
    Checks.COMMUNICABILITY.value,
    Checks.UPGRADE_ISO_VERSION.value
)

REPLACENODE_CHECKS = {
    Checks.STORAGE_LUNS.value,
    Checks.MGMT_VIP.value,
    Checks.BMC_ACCESSIBILITY.value,
    Checks.HOSTNAMES.value
}

DEPLOY_POST_CHECKS = {
    Checks.MGMT_VIP.value,
    Checks.PUB_DATA_IP.value,
    Checks.HOSTNAMES.value,
    Checks.CONNECTIVITY.value,
    Checks.PASSWORDLESS_SSH_ACCESS.value,
    Checks.COMMUNICABILITY.value,
    Checks.STORAGE_LVMS.value,
    Checks.STORAGE_LUNS.value,
    Checks.LUNS_MAPPED.value,
    Checks.CLUSTER_STATUS.value,
    Checks.LOGS_ARE_GOOD.value,
    Checks.BMC_ACCESSIBILITY.value
}

UNBOXING_PRE_CHECKS = {
    Checks.PUB_DATA_IP.value,
    Checks.HOSTNAMES.value,
    Checks.PASSWORDLESS_SSH_ACCESS.value,
    Checks.BMC_ACCESSIBILITY.value,
    Checks.STORAGE_LUNS.value,
    Checks.LUNS_MAPPED.value,
    Checks.CONTROLLER_IP.value,
}

UNBOXING_POST_CHECKS = {
    Checks.BMC_STONITH.value,
}


# validations parameters
NETWORK_DRIVER = "mlnx-ofed"
HCA_PROVIDER = ["mellanox"]
HBA_PROVIDER = ["lsi"]
LUNS_CHECKS = ['accessible', 'size']
LUNS_MAPPED_CHECK = "mapped"


class CheckVerdict(Enum):

    """Values which represent validation status"""
    PASSED = "passed"
    FAIL = "fail"


class ReleaseInfo(Enum):
    NAME = 'NAME'
    VERSION = 'VERSION'
    BUILD = 'BUILD'
    OS = 'OS'
    DATETIME = 'DATETIME'
    KERNEL = 'KERNEL'
    COMPONENTS = 'COMPONENTS'
    RELEASE = 'RELEASE'


# NOTE: for more convenient usage of check.CheckResult.get_checks method
CRITICALLY_FAILED = {"critical": True, "failed": False}
NON_CRITICALLY_FAILED = {"critical": False, "failed": True}

IS_REPO_KEY = "is_repo"


class CortxResourceT(Enum):

    """Resource types in CORTX provisioner"""

    REPOS = "cortx_repos"
    CONSUL = "consul"
    SALTSTACK = "saltstack"
    SALT_MASTER = "salt-master"
    SALT_MINION = "salt-minion"
    SALT_CLUSTER = "salt-cluster"
    PROVISIONER = "provisioner"
    PROVISIONER_API = "provisioner-api"


class ContentType(Enum):

    """File content type enumeration."""

    JSON = "json"
    YAML = "yaml"


class HashType(Enum):

    """Hash type enumeration."""

    MD5 = "md5"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"


# UPGRADE ROUTINE
class ConfigLevelT(Enum):
    """CORTX configuration levels"""
    CLUSTER = "cluster"
    NODE = "node"


class LockMetaDataFields(Enum):
    """Provisioner Lock Metadata fields."""

    PID = "pid"
    SOURCE_TARGET = "source_target"


class HACmdResult(Enum):
    """HA output for command results."""

    FAILED = 'failed'
    SUCCEEDED = 'succeeded'
    IN_PROGRESS = 'inprogress'


class HAClusterStatus(Enum):
    """HA output for cluster statuses."""

    ONLINE = 'online'
    OFFLINE = 'offline'
    STANDBY = 'standby'
    DEGRADED = 'degraded'


class ISOValidationFields(Enum):
    """Name of ISO validation fields."""

    STATUS = "Status"
    MSG = "msg"


class SWUpgradeInfoFields(Enum):
    """Named fields for meta information about SW upgrade repository"""

    VERSION = "version"
    VERSION_CONSTRAINT = "version_constraint"


class CortxFlows(Enum):

    """Cortx configuration flows."""

    DEPLOY = "deploy"
    UPGRADE = "upgrade"
    UPGRADE_OFFLINE = "upgrade-offline"


class MiniAPILevels(Enum):

    """Mini Provisioner API Levels."""

    CLUSTER = "cluster"
    NODE = "node"


class MiniAPISpecFields(Enum):

    """Mini Provisioner Top level spec fields."""

    VERSION = '__version__'
    DEFAULTS = '__defaults__'
    EVENTS = '__events__'
    CTX = '__context__'
    SUPPORT_BUNDLE = 'support_bundle'


class MiniAPISpecVersions(Enum):

    """Mini Provisioner specific versions."""

    INITIAL = '1.0'


class MiniAPISpecHookFields(Enum):

    """Mini Provisioner Hook spec fields."""

    CMD = 'cmd'
    ARGS = 'args'
    WHEN = 'when'


class MiniAPIBaseHooks(Enum):

    """Mini Provisioner API Hooks."""

    POST_INSTALL = 'post_install'
    PREPARE = 'prepare'
    CONFIG = 'config'
    INIT = 'init'
    TEST = 'test'
    UPGRADE = 'upgrade'
    RESET = 'reset'
    CLEANUP = 'cleanup'
    BACKUP = 'backup'
    RESTORE = 'restore'


class MiniAPIEvents(Enum):

    """Mini Provisioner API Events."""

    PRE = 'pre'
    POST = 'post'


def event_name(base_hook: MiniAPIBaseHooks, event: MiniAPIEvents):
    return f"{event.value}-{base_hook.value}"


MiniAPIHooks = Enum(
    'MiniAPIHooks',
    (
        [(k, v.value) for k, v in MiniAPIBaseHooks.__members__.items()] +
        [
            (event_name(*ev).upper().replace('-', '_'), event_name(*ev))
            for ev in itertools.product(MiniAPIBaseHooks, MiniAPIEvents)
        ]
    ),
    module=__name__
)
