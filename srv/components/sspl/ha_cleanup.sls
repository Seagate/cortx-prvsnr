{% if pillar['cluster'][grains['id']]['is_primary'] %}
HA cleanup for SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:ha-cleanup')
{% endif %}}
