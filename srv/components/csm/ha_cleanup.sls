{% if pillar['cluster'][grains['id']]['is_primary'] %}
HA cleanup for CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:ha-cleanup')
{% endif %}
