from pathlib import Path

PRVSNR_ROOT_DIR = Path('/opt/seagate/eos-prvsnr')

# reflects master file_roots configuration
PRVSNR_FILEROOTS_DIR = PRVSNR_ROOT_DIR / 'srv'
PRVSNR_USER_FILEROOTS_DIR = PRVSNR_ROOT_DIR / 'srv_user'
PRVSNR_USER_FILES_EOSUPDATE_REPOS_DIR = (
    PRVSNR_USER_FILEROOTS_DIR / 'misc_pkgs/eosupdate/repo/files'
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

ALL_MINIONS = '*'
LOCAL_MINION = '__local__'

PRVSNR_VALUES_PREFIX = 'PRVSNR_'
