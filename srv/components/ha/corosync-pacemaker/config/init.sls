include:
  - .base
  - .setup
{% if "physical" in grains['virtual'] %}
  - .clusterip
{% endif %}
