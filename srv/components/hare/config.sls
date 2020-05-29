{% if salt["grains.get"]('is_primary', false) %}
Stage - Post Install Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:post_install')

Stage - Configure Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:config')

Stage - Initialize Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:init')
{% endif %}
