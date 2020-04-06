include:
  - .base
{% if "physical" in grains['virtual'] %}
  - .cluster_ip
{% endif %}
