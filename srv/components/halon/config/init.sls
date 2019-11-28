include:
  - components.halon.config.base
{% if pillar['cluster'][grains['id']]['is_primary'] %}
  - components.halon.config.generate_facts
{% endif %}
