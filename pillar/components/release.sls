eos_release:
    target_build: http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/last_successful/
    update:
        base_dir: /opt/seagate/eos/updates
        repos: {}  # dictionary with (release, source) pairs,
                   # source should be either an url (starts with 'http://' or 'https://')
                   # or one of special values: 'dir', 'iso'
    commons:
        RedHat: http://ssc-nfs-server1.colo.seagate.com/releases/eos/uploads/rhel/rhel-7.7.1908/
        CentOS: http://ssc-nfs-server1.colo.seagate.com/releases/eos/uploads/centos/centos-7.7.1908/