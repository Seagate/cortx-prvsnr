{% if 'primary' in grains['roles'] 
  and if pillar['cluster']['mgmt_vip'] %}
Update Management VIP:
  cmd.run:
    - name: pcs resource update kibana-vip ip={{ pillar['cluster']['mgmt_vip'] }}

{% else %}

No Management VIP application:
  test.show_notification:
    - text: "Management VIP application only applies to primary node. Either this is not a primary node or value of Management Network VIP is missing in cluster pillar."

{% endif %}
