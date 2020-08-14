{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
include:
  - components.ha.ees_ha.prepare
  - components.ha.ees_ha.install
  - components.ha.ees_ha.config
{% else %}
setup LDR-R1 HA on non-primary node:
  test.show_notification:
    - text: "No changes needed on non-primary node"
{% endif %}

Generate ees_ha checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.ees_ha
    - makedirs: True
    - create: True
