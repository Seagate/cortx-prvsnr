{% if salt["grains.get"]('is_primary', false) %}
Stage - Test Hare:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup.yaml', 'hare:test')
{% endif %}
