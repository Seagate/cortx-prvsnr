{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.cortx-ha'.format(grains['id'])) %}
include:
  - components.ha.cortx-ha.prepare
  - components.ha.cortx-ha.install
  - components.ha.cortx-ha.config
  - components.ha.cortx-ha.ha

Generate ees_ha checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.cortx-ha
    - makedirs: True
    - create: True
{%- else -%}
cortx-ha already applied:
  test.show_notification:
    - text: "cortx-ha states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.ha.cortx-ha.teardown' to reprovision these states."
{%- endif -%}
