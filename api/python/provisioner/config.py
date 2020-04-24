from pathlib import Path

PRVSNR_ROOT_DIR = Path('/opt/seagate/eos-prvsnr')

# reflects master file_roots configuration
PRVSNR_FILEROOTS_DIR = PRVSNR_ROOT_DIR / 'srv'
PRVSNR_USER_FILEROOTS_DIR = PRVSNR_ROOT_DIR / 'srv_user'
#    relative paths
PRVSNR_USER_FILES_EOSUPDATE_REPOS_DIR = Path('misc_pkgs/eosupdate/repo/files')
PRVSNR_USER_FILES_SSL_CERTS_FILE = Path(
    'components/misc_pkgs/ssl_certs/files/stx.pem'
)
SSL_CERTS_FILE = Path('/etc/ssl/stx/stx.pem')

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
    'rabbitmq.sls',
    'release',
    'rsyslog.sls',
    's3clients',
    's3server',
    'sspl',
    'storage_enclosure.sls',
    'system',
    'uds'
]

CONTROLLER_A = 'a'
CONTROLLER_B = 'b'
CONTROLLER_BOTH = 'both'

PRVSNRUSERS_GROUP = 'prvsnrusers'
