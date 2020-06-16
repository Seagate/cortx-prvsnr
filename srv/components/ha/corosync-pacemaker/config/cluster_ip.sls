{% if "primary" in grains['roles'] -%}
{% if pillar['cluster']['cluster_ip'] -%}

{% if (0 == salt['cmd.retcode']('command -v pcs')) 
  and (0 == salt['cmd.retcode']('pcs resource show ClusterIP-clone')) -%}

Update ClusterIP:
  cmd.run:
    - name: pcs resource update ClusterIP ip={{ pillar['cluster']['cluster_ip'] }}
    - onlyif: pcs resource show ClusterIP

{% else %}  # Is pcs installed & ClusterIP exists
# Ensure ClusterIP absent before creating:
#   cmd.run:
#     - name: pcs resource delete ClusterIP
#     - onlyif: pcs resource show ClusterIP

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] -%}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
{%- endif -%}
Setup ClusterIP resouce:
  cmd.run:
    - name: pcs resource create ClusterIP ocf:heartbeat:IPaddr2 ip={{ pillar['cluster']['cluster_ip'] }} mac=$(echo "01:00:5e:`echo {{ grains['hwaddr_interfaces'][data_if] }} | cut -d ":" -f 1-3`") nic={{ data_if }} op monitor interval=30s

Add stickiness metadata to ClusterIP resource:
  cmd.run:
    - name: pcs resource meta ClusterIP resource-stickiness=0
    - require:
      - Setup ClusterIP resouce

Clone ClusterIP:
  cmd.run:
    - name: pcs resource clone ClusterIP clusterip_hash=sourceip-sourceport clone-max=2 clone-node-max=2 globally-unique=true priority=1
    # priority=1 above ensures that ClusterIP-clone is distributed across nodes.
    - requries:
      - Setup ClusterIP resouce
{% endif %} # Is pcs installed & ClusterIP exists
{% else %}  # Cluster IP available in pillar
Missing ClusterIP:
  test.fail_without_changes:
    - name: ClusterIP is blank in Cluster.sls. Please udpate with valid IP and re-run.
{% endif %}  # Cluster IP available in pillar
{% else %}  # Is node primary
No Cluster IP application:
  test.show_notification:
    - text: "Cluster IP application applies only to primary node. There's no execution on secondary node"
{% endif %}  # Is node primary
