from typing import Optional

from . import config
from .utils import dump_yaml, run_subprocess_cmd


# TODO TEST EOS-8473
def setup(profile_paths: Optional[dict] = None, clean=False):
    if profile_paths is None:
        profile_paths = config.profile_paths()

    if clean:
        run_subprocess_cmd(['rm', '-rf', str(profile_paths['base_dir'])])

    profile_paths['base_dir'].mkdir(parents=True, exist_ok=True)
    profile_paths['ssh_dir'].mkdir(parents=True, exist_ok=True)
    profile_paths['ssh_dir'].chmod(0o700)

    for path in (
        profile_paths['salt_dir'],
        profile_paths['salt_fileroot_dir'],
        profile_paths['salt_pillar_dir'],
        profile_paths['salt_cache_dir'],
        profile_paths['salt_pki_dir'],
        profile_paths['salt_config_dir']
    ):
        path.mkdir(parents=True, exist_ok=True)

    # config file for salt tools (salt-call, salt-ssh)
    # Note. for now the same for master (salt-ssh) and
    #       minion (salt-call --local) settings
    profile_config = {
        'pki_dir': str(profile_paths['salt_pillar_dir']),
        'cachedir': str(profile_paths['salt_cache_dir']),
        'file_roots': {
            'base': [
               str(profile_paths['salt_fileroot_dir']),
               str(config.BUNDLED_SALT_FILEROOT_DIR)
            ]
        },
        'pillar_roots': {
            'base': [
                str(config.BUNDLED_SALT_PILLAR_DIR),
                str(profile_paths['salt_pillar_dir'])
            ]
        }
    }
    # TODO IMPROVE ??? use symlink
    dump_yaml(profile_paths['salt_master_file'], profile_config)
    dump_yaml(profile_paths['salt_minion_file'], profile_config)

    # saltfile for salt tools
    saltfile = {
        'salt-ssh': {
            'config_dir': str(profile_paths['salt_config_dir']),
            'roster_file': str(profile_paths['salt_roster_file']),
            'ssh_log_file': str(profile_paths['salt_ssh_log_file'])
        },
        'salt-call': {
            'config_dir': str(profile_paths['salt_config_dir']),
            'log_file': str(profile_paths['salt_call_log_file'])
        }
    }
    dump_yaml(profile_paths['salt_salt_file'], saltfile)
