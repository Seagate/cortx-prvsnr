{% if pillar['cluster'][grains['id']]['is_primary'] %}
Setup UDS HA:
  cmd.run:
    - name: /opt/seagate/cortx/hare/libexec/build-ees-ha-uds
{% endif %}
