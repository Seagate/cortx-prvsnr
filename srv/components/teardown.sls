include:
  # Remove Management stack
  - components.csm.teardown
  - components.sspl.teardown
  # Remove IO Stack
  - components.ha.ees_ha.teardown
  - components.hare.teardown
  - components.s3server.teardown
  - components.eoscore.teardown
  # Remove pre-reqs
  - components.misc_pkgs.lustre.teardown
  - components.misc_pkgs.statsd.teardown
  - components.misc_pkgs.rabbitmq.teardown
  - components.misc_pkgs.openldap.teardown
  - components.misc_pkgs.nodejs.teardown
  - components.misc_pkgs.kibana.teardown
  - components.misc_pkgs.elasticsearch.teardown
  - components.ha.haproxy.teardown
  - components.ha.corosync-pacemaker.teardown
  - components.misc_pkgs.build_ssl_cert_rpms.teardown
  - components.system.storage.teardown
  # - components.system.mlnx_driver.teardown
  - components.system.chrony.teardown
  - components.system.logrotate.teardown
  - components.system.firewall.teardown
  - components.system.teardown
