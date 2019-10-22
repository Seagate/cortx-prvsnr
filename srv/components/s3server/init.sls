include:
  - components.misc.build_ssl_cert_rpms
  - components.ha.haproxy
  - components.misc.openldap
  # - components.ha.keepalived
  - components.s3server.prepare
  - components.s3server.install
  - components.s3server.config
  - components.s3server.start
  - components.s3server.housekeeping
  - components.s3server.sanity_check
