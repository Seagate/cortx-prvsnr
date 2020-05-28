{% if grains['is_primary'] %}
Setup UDS HA:
  cmd.run:
    - name: /opt/seagate/eos/hare/libexec/build-ees-ha-uds
{% endif %}
