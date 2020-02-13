{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
include:
  - components.ha.ees_ha.prepare
  - components.ha.ees_ha.config
{% else %}
setup EES HA on non-primary node:
  test.show_notification:
    - text: "No changes needed on non-primary node"
{% endif %}
