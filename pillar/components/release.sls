release:
    target_build: http://cortx-storage.colo.seagate.com/releases/eos/github/release/rhel-7.7.1908/last_successful/
    update:
        base_dir: /opt/seagate/cortx/updates
        repos: {}  # dictionary with (release, source) pairs,
                   # source should be either an url (starts with 'http://' or 'https://')
                   # or one of special values: 'dir', 'iso'
