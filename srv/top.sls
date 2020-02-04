base:
  '*':
    - components.system
    # Dependecies
    - components.misc_pkgs.build_ssl_cert_rpms
    # - components.misc_pkgs.consul
    - components.ha.corosync-pacemaker
    - components.misc_pkgs.elasticsearch
    - components.misc_pkgs.kibana
    - components.misc_pkgs.nodejs
    - components.misc_pkgs.rabbitmq
    - components.misc_pkgs.statsd
    - components.misc_pkgs.openldap
    - components.ha.haproxy
    # IO Stack
    - components.eoscore
    - components.s3server
    - components.hare
    - components.post_setup
    # Management Stack
    - components.sspl
    - components.csm
