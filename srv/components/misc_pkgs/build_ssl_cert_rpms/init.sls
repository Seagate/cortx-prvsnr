{% set node = grains['id'] %}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(node), false) %}

include:
  - components.misc_pkgs.build_ssl_cert_rpms.install
  - components.misc_pkgs.build_ssl_cert_rpms.prepare
  - components.misc_pkgs.build_ssl_cert_rpms.config
  - components.misc_pkgs.build_ssl_cert_rpms.housekeeping
  - components.misc_pkgs.build_ssl_cert_rpms.sanity_check

{% else %}

# Fetch fqdn of primary node
Copy certs from primary:
  cmd.run:
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if pillar['cluster'][node_id]['is_primary'] %}
    - name: scp {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/stx-s3-*.rpm /opt/seagate
{%- endif -%}
{%- endfor -%}

{% endif %}
