{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.kibana'.format(grains['id'])) %}
include:
  - components.misc_pkgs.kibana.prepare
  - components.misc_pkgs.kibana.install
  - components.misc_pkgs.kibana.config
  - components.misc_pkgs.kibana.start
  - components.misc_pkgs.kibana.housekeeping
  - components.misc_pkgs.kibana.sanity_check

Generate Kibana checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.kibana
    - makedirs: True
    - create: True
{%- else -%}
Kibana already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.kibana.teardown' to reprovision these states."
{% endif %}