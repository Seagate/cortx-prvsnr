base:
  '*':
    - components.system
    - components.system.storage
    # Dependecies
    - components.misc_pkgs.build_ssl_cert_rpms
    - components.misc_pkgs.rsyslog
    - components.ha.corosync-pacemaker
    - components.ha.haproxy
    - components.misc_pkgs.elasticsearch
    - components.misc_pkgs.kibana
    - components.misc_pkgs.nodejs
    - components.misc_pkgs.openldap
    - components.misc_pkgs.rabbitmq
    - components.misc_pkgs.statsd
    # IO Stack
    - components.misc_pkgs.lustre
    - components.eoscore
    - components.s3server
    - components.hare
    # Management Stack
    - components.sspl
    - components.csm
