{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.cortx-moto'.format(grains['id'])) %}
include:
  - components.cortx-moto.prepare
  - components.cortx-moto.install
  - components.cortx-moto.config
  # - components.cortx-moto.start
  - components.cortx-moto.sanity_check

Generate cortx-moto checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.cortx-moto
    - makedirs: True
    - create: True

{%- else -%}

cortx-moto already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.cortx-moto.teardown' to reprovision these states."

{%- endif %}
