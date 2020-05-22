{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.storage'.format(grains['id'])) %}
include:
  - components.system.storage.prepare
  - components.system.storage.install
  - components.system.storage.config

Generate storage checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.storage
    - makedirs: True
    - create: True
{%- else -%}
Storage already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.system.storage.teardown' to reprovision these states."
{% endif %}
