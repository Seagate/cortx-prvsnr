{% if 'physical' in grains['virtual'] %}
include:
  - .prepare
  - .config
{% endif %}
