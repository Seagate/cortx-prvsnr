from pathlib import Path

# TODO
#  - rename to defaults.py or constants.py or ...
#  - then rename base.py to config.py
#  - remove PRVSNR_ prefix

PRVSNR_ROOT_DIR = Path('/opt/seagate/eos-prvsnr')

# reflects master file_roots configuration
PRVSNR_FILEROOTS_DIR = PRVSNR_ROOT_DIR / 'srv'
PRVSNR_USER_FILEROOTS_DIR = PRVSNR_ROOT_DIR / 'srv_user'
#    relative paths
PRVSNR_USER_FILES_EOSUPDATE_REPOS_DIR = Path('misc_pkgs/eosupdate/repo/files')
PRVSNR_USER_FILES_SSL_CERTS_FILE = Path(
    'components/misc_pkgs/ssl_certs/files/stx.pem'
)

# reflects pillar/top.sls
PRVSNR_PILLAR_DIR = PRVSNR_ROOT_DIR / 'pillar'
PRVSNR_USER_PILLAR_DIR = PRVSNR_PILLAR_DIR / 'user'
PRVSNR_USER_PI_ALL_HOSTS_DIR = PRVSNR_USER_PILLAR_DIR / 'groups/all'
PRVSNR_DEF_PI_HOST_DIR_TMPL = str(
    PRVSNR_PILLAR_DIR / 'minions/{minion_id}'
)
PRVSNR_USER_PI_HOST_DIR_TMPL = str(
    PRVSNR_USER_PILLAR_DIR / 'minions/{minion_id}'
)

SEAGATE_USER_HOME_DIR = Path('/opt/seagate/users')
SEAGATE_USER_FILEROOTS_DIR_TMPL = str(
    'components/provisioner/files/users/{uname}'
)

ALL_MINIONS = '*'
LOCAL_MINION = '__local__'

PRVSNR_VALUES_PREFIX = 'PRVSNR_'

# TODO ??? make that dynamic (based on pillar structure)
PRVSNR_EOS_COMPONENTS = [
    'cluster',
    'commons',
    'controller',
    'corosync-pacemaker',
    'elasticsearch',
    'eoscore',
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
# FIXME logfiles path set to /tmp reason EOS-9529
LOG_ROOT_DIR = Path('/tmp')
if not LOG_ROOT_DIR.exists():
    LOG_ROOT_DIR = Path('.').resolve()

LOG_NULL_HANDLER = '_null'
LOG_CONSOLE_HANDLER = 'console'
LOG_FILE_HANDLER = 'logfile'
LOG_CMD_FILTER = 'cmd_filter'
#   logfile habdler for the following commands
#   will be enabled forcibly
LOG_FORCED_LOGFILE_CMDS = [
    'set_network',
    'set_eosupdate_repo',
    'eos_update',
    'fw_update',
    'set_ssl_certs',
    'reboot_server',
    'reboot_controller',
    'shutdown_controller',
    'create_user'
]
