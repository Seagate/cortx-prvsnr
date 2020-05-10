{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.uds'.format(grains['id'])) %}
include:
  - .prepare
  - .install
  - .config

Generate uds checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.uds
    - makedirs: True
    - create: True

{%- else -%}

UDS already applied:
  test.show_notification:
    - text: "UDS states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.uds.teardown' to reprovision these states."

{%- endif -%}
