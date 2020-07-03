{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.multipath'.format(grains['id'])) %}
include:
{% if "physical" in grains['virtual'] %}
  - components.system.storage.teardown.tidy-up
{% endif %}
  - components.system.storage.multipath.prepare
  - components.system.storage.multipath.install
  - components.system.storage.multipath.config

Generate multipath checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.multipath
    - makedirs: True
    - create: True
{%- else -%}
multipath already applied:
  test.show_notification:
    - text: "multipath states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.system.multipath.teardown' to reprovision these states."
{% endif %}
