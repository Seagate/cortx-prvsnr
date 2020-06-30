{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.motr'.format(grains['id'])) %}
include:
  - components.motr.prepare
  - components.motr.install
  - components.motr.config
  # - components.motr.start
  - components.motr.sanity_check

Generate motr checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.motr
    - makedirs: True
    - create: True

{%- else -%}

motr already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.motr.teardown' to reprovision these states."

{%- endif %}
