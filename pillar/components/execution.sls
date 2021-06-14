execution:
  noncortx_components:
    platform:
      - system
      - system.storage.multipath
      - system.storage
      - misc_pkgs.rsyslog
      - system.logrotate
    3rd_party:
      - misc_pkgs.sos
      - misc_pkgs.ipmi.bmc_watchdog
      - misc_pkgs.ssl_certs
      - ha.haproxy
      - misc_pkgs.openldap
      - misc_pkgs.nodejs
      - misc_pkgs.kafka
      - misc_pkgs.elasticsearch
      - misc_pkgs.kibana
      - misc_pkgs.statsd
      - misc_pkgs.consul.install
      - misc_pkgs.lustre
      - misc_pkgs.consul.install
      - ha.corosync-pacemaker.install
      - ha.corosync-pacemaker.config.base
  cortx_components:
    foundation:
      - cortx_utils
    iopath:
      - motr
      - s3server
      - hare
    controlpath:
      - sspl
      - uds
      - csm
    ha:
      - cortx_ha

