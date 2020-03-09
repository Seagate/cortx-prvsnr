{% if pillar['cluster'][grains['id']]['is_primary'] -%}
{% if pillar['cluster']['cluster_ip'] %}
Create CIB for ClusterIP:
  cmd.run:
    - name: pcs cluster cib /tmp/loadbalance_cfg
    - unless: pcs resource show ClusterIP

# Create CIB for ClusterIP:
#   pcs.cib_present:
#       - name: create_cib_for_clusterip_cib_present_loadbalance_cfg
#       - cibname: /tmp/loadbalance_cfg
#       - scope: None
#       - extra_args: None

Setup ClusterIP resouce:
  cmd.run:
    - name: pcs -f /tmp/loadbalance_cfg resource create ClusterIP ocf:heartbeat:IPaddr2 ip={{ pillar['cluster']['cluster_ip'] }} nic=data0 op monitor interval=30s
    - require:
      - Create CIB for ClusterIP

# Setup ClusterIP resouce:
#   pcs.resource_present:
#     - resource_id: ClusterIP
#     - resource_type: "ocf:heartbeat:IPaddr2"
#     - resource_options:
#       - ip={{ pillar['cluster']['cluster_ip'] }}
#       - op monitor interval=30s
#     - cibname: /tmp/loadbalance_cfg

Clone ClusterIP:
  cmd.run:
    - name: pcs -f /tmp/loadbalance_cfg resource clone ClusterIP clusterip_hash=sourceip clone-max=2 clone-node-max=2
    - requries:
      - Setup ClusterIP resouce

Push CIB to all nodes:
  cmd.run:
    - name: pcs cluster cib-push /tmp/loadbalance_cfg --config
    - require:
      - Clone ClusterIP

# Push CIB to all nodes:
#   pcs.cib_pushed:
#     - cibname: /tmp/loadbalance_cfg
#     - scope: None
#     - extra_args:
#       - '--config'
#     - require:
#         - Clone ClusterIP

Remove CIB file:
  file.absent:
    - name: /tmp/loadbalance_cfg

{% else %}}
Missing ClusterIP:
  test.fail_without_changes:
    - name: ClusterIP is blank in Cluster.sls. Please udpate with valid IP and re-run.
{% endif %}
{% endif %}
