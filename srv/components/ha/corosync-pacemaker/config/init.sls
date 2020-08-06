include:
  - .base
  - .setup_cluster
{% if "physical" in grains['virtual'] %}
  - .cluster_ip
{% if pillar['cluster'][grains['id']]['bmc']['ip'] %}
  - .stonith
{% endif %}
{% endif %}
