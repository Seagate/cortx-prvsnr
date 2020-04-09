{% if pillar['cluster'][grains['id']]['is_primary'] -%}
{%- if pillar['cluster']['mgmt_vip'] %}
Update Management VIP:
  cmd.run:
    - name: pcs resource update kibana-vip ip={{ pillar['cluster']['mgmt_vip'] }}
{% else %}
Missing Management VIP:
  test.fail_without_changes:
    - name: Management VIP is blank in Cluster.sls. Please udpate with valid IP and re-run.
{% endif %}
{% else %}
No Management VIP application:
  test.show_notification:
    - text: "Management VIP application only applies to primary node. There's no execution on secondary node"
{% endif %}
