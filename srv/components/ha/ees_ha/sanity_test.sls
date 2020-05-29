{% if salt["grains.get"]('is_primary', false) %}
start EES HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:test')
{% endif %}
