{% if grains['is_primary'] %}
HA cleanup for SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:ha-cleanup')
{% else %}
No post install for SSPL:
  test.show_notification:
    - text: "Post install for SSPL only applies to primary node. There's no execution on secondary node"
{% endif %}
