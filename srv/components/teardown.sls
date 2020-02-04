include:
  # Remove Management stack
  - components.csm.teardown
  - components.sspl.teardown
  # Remove IO Stack
  - components.hare.teardown
  - components.s3server.teardown
  - components.eoscore.teardown
  # Remove pre-reqs
  - components.ha.haproxy.teardown
  - components.ha.corosync-pacemaker.teardown
  - components.misc_pkgs.openldap.teardown
  - components.misc_pkgs.statsd.teardown
  - components.misc_pkgs.rabbitmq.teardown
  - components.misc_pkgs.nodejs.teardown
  - components.misc_pkgs.kibana.teardown
  - components.misc_pkgs.elasticsearch.teardown
  - components.misc_pkgs.build_ssl_cert_rpms.teardown
