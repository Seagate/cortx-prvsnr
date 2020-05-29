{% if salt["grains.get"]('is_primary', false) %}
include:
  - components.ha.ees_ha.prepare
  - components.ha.ees_ha.install
  - components.ha.ees_ha.config
{% else %}
setup EES HA on non-primary node:
  test.show_notification:
    - text: "No changes needed on non-primary node"
{% endif %}

Generate ees_ha checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.ees_ha
    - makedirs: True
    - create: True
