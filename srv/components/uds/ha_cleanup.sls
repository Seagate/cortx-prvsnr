{% if pillar['cluster'][grains['id']]['is_primary'] %}
Teardown UDS HA:
  cmd.run:
    - name: /opt/seagate/eos/hare/libexec/prov-ha-uds-reset
    - onlyif: test -x /opt/seagate/eos/hare/libexec/prov-ha-uds-reset
{% endif %}
