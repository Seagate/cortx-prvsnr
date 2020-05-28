{% if grains['is_primary'] %}
HA cleanup for CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:ha-cleanup')
{% else %}
No HA cleanup for CSM:
  test.show_notification:
    - text: "HA cleanup for CSM only applies to primary node. There's no execution on secondary node"
{% endif %}
