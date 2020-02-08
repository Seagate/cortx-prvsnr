{% set node = grains['id'] %}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(node), false) %}

include:
  - components.misc_pkgs.build_ssl_cert_rpms.install
  - components.misc_pkgs.build_ssl_cert_rpms.prepare
  - components.misc_pkgs.build_ssl_cert_rpms.config
  - components.misc_pkgs.build_ssl_cert_rpms.housekeeping
  - components.misc_pkgs.build_ssl_cert_rpms.sanity_check

# Copy generated cert from Master
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if not pillar['cluster'][node_id]['is_primary'] %}
# Requries pip install scp
# Copy certs to non-primary:
#   module.run:
#     - scp.put:
#       - files:
#         - /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm
#         - /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
#       - remote_path: /opt/seagate
#       - recursive: True
#       - preserve_times: True
#       - hostname: pillar['cluster'][node_id]['hostname']
#       - auto_add_policy: True

Copy certs to non-primary:
  cmd.run:
    - name: scp /opt/seagate/stx-s3-*.rpm {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/

{%- endif -%}
{%- endfor -%}
{% endif %}
