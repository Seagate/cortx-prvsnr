{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.cortx-motr'.format(grains['id'])) %}
include:
  - components.cortx-motr.prepare
  - components.cortx-motr.install
  - components.cortx-motr.config
  # - components.cortx-motr.start
  - components.cortx-motr.sanity_check

Generate cortx-motr checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.cortx-motr
    - makedirs: True
    - create: True

{%- else -%}

cortx-motr already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.cortx-motr.teardown' to reprovision these states."

{%- endif %}
