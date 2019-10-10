{% set node = grains['id'] %}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(node), false) %}

include:
  - components.misc.build_ssl_cert_rpms.install
  - components.misc.build_ssl_cert_rpms.prepare
  - components.misc.build_ssl_cert_rpms.config
  - components.misc.build_ssl_cert_rpms.housekeeping
  - components.misc.build_ssl_cert_rpms.sanity_check

{% else %}

# Fetch fqdn of primary node
Copy certs from primary:
  cmd.run:
    - name: scp {{ opts['master'] }}:/opt/seagate/stx-s3-*.rpm /opt/seagate

{% endif %}
