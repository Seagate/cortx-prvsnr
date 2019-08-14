{% set node = grains['id'] %}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(node), false) %}

include:
  - components.s3server.build_ssl_cert_rpms.install
  - components.s3server.build_ssl_cert_rpms.prepare
  - components.s3server.build_ssl_cert_rpms.config
  - components.s3server.build_ssl_cert_rpms.housekeeping
  - components.s3server.build_ssl_cert_rpms.sanity_check

{% else %}

# Fetch fqdn of primary node
{% for node_id in pillar['cluster']['node_list'] %}
  {% if salt['pillar.get']('cluster:{0}:is_primary'.format(node_id), None) %}

Copy certs from primary:
  cmd.run:
    - name: scp {{ pillar['cluster'][node_id]['fqdn'] }}:/opt/seagate/stx-s3-*.rpm /opt/seagate

  {% endif %}
{% endfor %}
{% endif %}
