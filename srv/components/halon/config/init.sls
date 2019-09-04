include:
  - components.halon.config.base
{% if pillar['cluster']['type'] == "single" %}
  - components.halon.config.generate_facts
{% endif %}
