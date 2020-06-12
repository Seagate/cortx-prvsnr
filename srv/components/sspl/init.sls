{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.sspl'.format(grains['id'])) %}
include:
  - components.sspl.prepare
  - components.sspl.install
  - components.sspl.config
  - components.sspl.start
#  - components.sspl.sanity_check

Generate sspl checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.sspl
    - makedirs: True
    - create: True
    - order: last

{%- else -%}

SSPL already applied:
  test.show_notification:
    - text: "SSPL states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.sspl.teardown' to reprovision these states."

{%- endif -%}
