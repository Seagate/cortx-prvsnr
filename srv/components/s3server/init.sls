include:
  # - components.ha.haproxy
  # - components.misc_pkgs.openldap
  
  # - components.ha.keepalived
  - components.s3server.prepare
  - components.s3server.install
  - components.s3server.config
  - components.s3server.start
  - components.s3server.housekeeping
  - components.s3server.sanity_check
