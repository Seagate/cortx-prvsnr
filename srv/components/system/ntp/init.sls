{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.ntp'.format(grains['id'])) %}
include:
  - components.system.ntp.install
  - components.system.ntp.prepare
  - components.system.ntp.config
  - components.system.ntp.start

Generate ntp checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.ntp
    - makedirs: True
    - create: True

{%- else -%}
ntp already applied:
  test.show_notification:
    - text: "ntp states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.system.ntp.teardown' to reprovision these states."
{% endif %}