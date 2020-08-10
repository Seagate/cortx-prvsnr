{% if pillar['cluster'][grains['id']]['is_primary'] %}
Stage - Test CSM HA:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/csm/conf/setup.yaml', 'csm:ha_sanity')
{% else %}
Stage - Test CSM HA:
  test.show_notification:
    - text: "HA Sanity for CSM only applies to primary node."
{% endif %}
