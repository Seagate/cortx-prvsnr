{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.lustre'.format(grains['id'])) %}
include:
  - components.misc_pkgs.lustre.prepare
  - components.misc_pkgs.lustre.install
  - components.misc_pkgs.lustre.config
  - components.misc_pkgs.lustre.start
  - components.misc_pkgs.lustre.sanity_check

Generate lustre checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.lustre
    - makedirs: True
    - create: True
{%- else -%}
Lustre already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.lustre.teardown' to reprovision these states."
{% endif %}
