{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Stage - Post Install Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/hare/conf/setup.yaml', 'hare:post_install')

Stage - Configure Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/hare/conf/setup.yaml', 'hare:config')

Stage - Initialize Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/hare/conf/setup.yaml', 'hare:init')
{% endif %}
