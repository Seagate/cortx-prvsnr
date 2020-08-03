# This state file is ignored if run on replacement node
{% if not salt["environ.get"]('REPLACEMENT_NODE', false) %}     # replacement node check
{% if grains['roles'][0] -%}                                    # priamry node check
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

Ignore the Quorum Policy:
  pcs.prop_has_value:
    - prop: no-quorum-policy
    - value: ignore

Enable STONITH:
  pcs.prop_has_value:
    - prop: stonith-enabled
{% if pillar['cluster'][grains['id']]['bmc']['ip'] %}
    - value: true     # Set only if BMC IP is specified
{% else %}
    - value: false
{% endif %}
{% else %}            # Check for is node primary
No Cluster Setup:
  test.show_notification:
    - text: "Cluster setup applies only to primary node. There's no Cluster setup operation on secondary node"
{%- endif -%}
{%- endif -%}         # replacement node check
