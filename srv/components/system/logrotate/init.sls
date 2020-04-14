{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.logrotate'.format(grains['id'])) %}
include:
  - components.system.logrotate.install
  - components.system.logrotate.config

Generate logrotate checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.logrotate
    - makedirs: True
    - create: True
{%- else -%}
logrotate already applied:
  test.show_notification:
    - text: "logrotate states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.system.logrotate.teardown' to reprovision these states."
{% endif %}