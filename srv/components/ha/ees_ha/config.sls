{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
include:
  - components.ha.ees_ha.prepare
  - components.ha.ees_ha.install

Post install for LDR-R1 HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ees.yaml', 'ees-ha:post_install')

Config for LDR-R1 HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ees.yaml', 'ees-ha:config')

start LDR-R1 HA cluster:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ees.yaml', 'ees-ha:init')
{% endif %}
