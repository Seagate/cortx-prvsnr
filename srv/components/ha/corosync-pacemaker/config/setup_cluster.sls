# This state file is ignored if run on replacement node
# replacement node check & priamry node check
{% if not salt["environ.get"]('REPLACEMENT_NODE')
  and 'primary' in grains['roles'] -%}
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

{% set stonith-enabled = false %}
{% if pillar['cluster'][grains['id']]['bmc']['ip']
  and "physical" in grains['virtual'] %}
{% set stonith-enabled = true %}
{% endif %}

Enable STONITH:
  pcs.prop_has_value:
    - prop: stonith-enabled
    - value: {{ stonith-enabled }}     # Set only if BMC IP is specified

{% else %}            # Check for is node primary

No Cluster Setup:
  test.show_notification:
    - text: "Cluster setup applies only to primary node. There's no Cluster setup operation on secondary node"

{%- endif -%}         # Check: Is node primary & is replacement node
