{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
start LDR-R1 HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ees.yaml', 'ees-ha:test')
{% endif %}
