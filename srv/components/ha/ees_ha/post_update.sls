{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Stage - Post Update Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/hare/conf/setup-ha.yaml', 'hare:post_update')
{% endif %}
