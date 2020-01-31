base:
  '*':
    - components.system
    - components.misc_pkgs.build_ssl_cert_rpms
    - components.misc_pkgs.openldap
    - components.ha.haproxy
    - components.eoscore
    - components.s3server
    - components.hare
    - components.post_setup
    - components.sspl
    - components.csm
