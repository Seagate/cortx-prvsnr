eos_release:
    type: internal  # value 'public' will switch to publicly hosted
                    # repo structure assumptions, where 'target_build'
                    # defines the base url of the hosted artifcats:
                    # <base_url>/
                    #   rhel7.7 or centos7.7   <- OS ISO is mounted here
                    #   3rd_party              <- CORTX 3rd party ISO is mounted here
                    #   cortx_iso              <- CORTX ISO (main) is mounted here
    target_build: http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/last_successful/
    update:
        base_dir: /opt/seagate/eos/updates
        repos: {}  # dictionary with (release, source) pairs,
                   # source should be either an url (starts with 'http://' or 'https://')
                   # or one of special values: 'dir', 'iso'
