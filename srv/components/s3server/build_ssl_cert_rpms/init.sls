{% set node = 'node_1' if grains['fqdn'] == pillar['facts']['node_1']['fqdn'] else 'node_2' if grains['fqdn'] == pillar['facts']['node_2']['fqdn'] else None %}
{% if salt["pillar.get"]('facts:{0}:primary'.format(node), false) %}
include:
  - components.s3server.build_ssl_cert_rpms.install
  - components.s3server.build_ssl_cert_rpms.prepare
  - components.s3server.build_ssl_cert_rpms.config
  - components.s3server.build_ssl_cert_rpms.housekeeping
  - components.s3server.build_ssl_cert_rpms.sanity_check
{% else %}
Copy certs from primary:
  cmd.run:
    - name: scp {{ pillar['facts'][node]['fqdn'] }}:/opt/seagate/stx-s3-*.rpm /opt/seagate
{% endif %}
