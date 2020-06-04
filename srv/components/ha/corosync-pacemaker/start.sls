# start corosync-pacemaker through pcs
{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Start corosync-pacemaker:
  cmd.run:
    - name: pcs cluster start --all
{% else %}
Start corosync-pacemaker:
  test.show_notification:
    - text: "Start corosync-pacemaker applies only to primary node. There's no cluster start operation on secondary node"
{% endif %}
