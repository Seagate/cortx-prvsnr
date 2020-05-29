{% if grains['is_primary'] %}
include:
  - components.ha.ees_ha.prepare

Run cortx-ha ha setup:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:ha-cleanup')
    - require:
      - Render ha input params template
{% else %}
No HA cleanup on secondary node:
  test.show_notification:
    - text: "HA cleanup  applies to primary node. There's no execution on secondary node"
{% endif %}
