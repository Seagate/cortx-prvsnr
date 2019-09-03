include:
  - components.halon.base
{% if pillar['cluster']['type'] == "single" %}
  - components.halon.config.generate_facts
{% endif %}