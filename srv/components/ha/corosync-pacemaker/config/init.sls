include:
  - .base
{% if "physical" in grains['virtual'] %}
  - .cluster_ip
{% if pillar['cluster'][grains['id']]['bmc']['ip'] %}
  - .stonith
{% endif %}
{% endif %}
