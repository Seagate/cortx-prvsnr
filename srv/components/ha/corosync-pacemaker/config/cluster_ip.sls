{% if grains['is_primary'] -%}
{% if pillar['cluster']['cluster_ip'] %}
Ensure ClusterIP absent before creating:
  cmd.run:
    - name: pcs resource delete ClusterIP
    - onlyif: pcs resource show ClusterIP

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] -%}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
{%- endif -%}
{%- set mac_addr = grains['hwaddr_interfaces'][data_if] -%}
Setup ClusterIP resouce:
  cmd.run:
    - name: pcs resource create ClusterIP ocf:heartbeat:IPaddr2 ip={{ pillar['cluster']['cluster_ip'] }} mac=$(echo "01:00:5e:`echo {{ mac_addr }} | cut -d ":" -f 1-3`") nic={{ data_if }} op monitor interval=30s

Add stickiness metadata to ClusterIP resource:
  cmd.run:
    - name: pcs resource meta ClusterIP resource-stickiness=0
    - require:
      - Setup ClusterIP resouce

Clone ClusterIP:
  cmd.run:
    - name: pcs resource clone ClusterIP clusterip_hash=sourceip-sourceport clone-max=2 clone-node-max=2 globally-unique=true
    - requries:
      - Setup ClusterIP resouce

{% else %}
Missing ClusterIP:
  test.fail_without_changes:
    - name: ClusterIP is blank in Cluster.sls. Please udpate with valid IP and re-run.
{% endif %}
{% else %}
No Cluster IP application:
  test.show_notification:
    - text: "Cluster IP application only applies to primary node. There's no execution on secondary node"
{% endif %}
