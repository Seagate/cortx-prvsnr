{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Remove Cortx-HA resources:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ees.yaml', 'ees-ha:reset')
    - order: 1
{% endif %}
Delete ees_ha checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.ees_ha
