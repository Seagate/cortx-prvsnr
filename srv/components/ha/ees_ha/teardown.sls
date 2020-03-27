{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Remove EOS-HA resources:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:reset')
    - order: 1
{% endif %}
Delete ees_ha checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.ees_ha

