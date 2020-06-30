{% if pillar['cluster'][grains['id']]['is_primary'] %}
Teardown UDS HA:
  cmd.run:
    - name: /opt/seagate/cortx/hare/libexec/prov-ha-uds-reset
    - onlyif: test -x /opt/seagate/cortx/hare/libexec/prov-ha-uds-reset
{% endif %}
