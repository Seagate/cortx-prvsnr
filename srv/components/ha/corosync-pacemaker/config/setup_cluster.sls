{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Setup Cluster:
  pcs.cluster_setup:
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ node_id }}
      {%- endfor %}
    - pcsclustername: {{ pillar['corosync-pacemaker']['cluster_name'] }}
    - extra_args:
      - '--start'
      - '--enable'
      - '--force'
{% else %}
No Cluster Setup:
  test.show_notification:
    - text: "Cluster setup applies only to primary node. There's no Cluster setup operation on secondary node"
{%- endif -%}
