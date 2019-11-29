include:
  - components.halon.teardown
  
  - components.misc.openldap.teardown
  - components.ha.haproxy.teardown
  - components.ha.keepalived.teardown
  - components.s3server.teardown
  - components.misc.build_ssl_cert_rpms.teardown

  - components.eoscore.teardown
  - components.sspl.teardown
  