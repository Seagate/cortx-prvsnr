{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
include:
  - components.ha.ees_ha.prepare
  - components.ha.ees_ha.install
<<<<<<< HEAD

Post install for EES HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:post_install')
    
Config for EES HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:config')
=======
>>>>>>> EOS-5962: Direct network config.

start EES HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:init')
<<<<<<< HEAD
=======
    - require:
      - pkg: Install hare
>>>>>>> EOS-5962: Direct network config.
{% endif %}