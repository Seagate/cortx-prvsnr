eos_release:
    target_build: http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/last_successful/
    update:
        base_dir: /opt/seagate/cortx/updates
        repos: {}  # dictionary with (release, source) pairs,
                   # source should be either an url (starts with 'http://' or 'https://')
                   # or one of special values: 'dir', 'iso'
