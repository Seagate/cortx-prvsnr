{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.consul'.format(grains['id'])) %}
include:
  - components.misc_pkgs.consul.prepare
  - components.misc_pkgs.consul.install
  - components.misc_pkgs.consul.config
  - components.misc_pkgs.consul.start
  - components.misc_pkgs.consul.housekeeping
  - components.misc_pkgs.consul.sanity_check

Generate Consul checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.consul
    - makedirs: True
    - create: True
{%- else -%}
Consul already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ node }}. execute 'salt '*' state.apply components.misc_pkgs.consul.teardown' to reprovision these states."
{% endif %}
