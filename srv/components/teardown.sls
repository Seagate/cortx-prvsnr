include:
  - components.hare.teardown
  
  - components.misc_pkgs.openldap.teardown
  - components.ha.haproxy.teardown
  - components.ha.keepalived.teardown
  - components.s3server.teardown
  - components.misc_pkgs.build_ssl_cert_rpms.teardown

  - components.eoscore.teardown
  - components.sspl.teardown
  