commons:
  cortx_commons:
    # includes different 3rd party artifacts
    # (multiple rpm repositories, raw archives, bash scirpts etc.)
    RedHat: http://cortx-storage.colo.seagate.com/releases/cortx/uploads/rhel/rhel-7.7.1908/
    CentOS: http://cortx-storage.colo.seagate.com/releases/cortx/uploads/centos/centos-7.7.1908/
  version:
    erlang: latest
    elasticsearch: 6.8.8-1
    rabbitmq: latest
    nodejs: v12.13.0
    rsyslog: 8.40.0-1.el7
    rsyslog-elasticsearch: 8.40.0-1.el7
    rsyslog-mmjsonparse: 8.40.0-1.el7
  repo:
    # base urls for lustre yum repositories (one per different networks: tcp, o2ib)
    # TODO IMPROVE EOS-12508 remove, should be related to cortx_common
    lustre: http://cortx-storage.colo.seagate.com/releases/cortx/lustre/custom/
