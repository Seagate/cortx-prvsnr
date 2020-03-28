include:
  - .base
  - .setup
{% if "physical" in grains['virtual'] %}
  - .cluster_ip
{% endif %}
