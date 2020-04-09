{% if pillar['cluster'][grains['id']]['is_primary'] %}
Post install for CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:ha')
{% else %}
No post install for CSM:
  test.show_notification:
    - text: "Post install for CSM only applies to primary node. There's no execution on secondary node"
{% endif %}
