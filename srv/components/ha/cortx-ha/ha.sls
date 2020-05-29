{% if grains['is_primary'] %}
include:
  - components.ha.cortx-ha.install
  - components.ha.ees_ha.prepare

Run cortx-ha HA setup:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:ha')
    - require:
      - Install cortx-ha
      - Render ha input params template
{% else %}
No HA setup on secondary node:
  test.show_notification:
    - text: "HA setup applies to primary node. There's no execution on secondary node"
{% endif %}
