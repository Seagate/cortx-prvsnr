{% if pillar['cluster'][grains['id']]['is_primary'] %}
Setup UDS HA:
  cmd.run:
    - name: /opt/seagate/cortx/ha/conf/script/build-ees-ha-uds
{% else %}
No post install for UDS:
  test.show_notification:
    - text: "Post install for UDS only applies to primary node. There's no execution on secondary node"
{% endif %}
