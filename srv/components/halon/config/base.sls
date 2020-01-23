{% import_yaml 'components/defaults.yaml' as defaults -%}

# logrotate.d
Setup logrotate policy for halon decision log:
  file.managed:
  - name: /etc/logrotate.d/halon
  - source: salt://components/halon/files/etc/logrotate.d/halon
  - keep_source: False

{% if 'mgmt0' in grains['ip4_interfaces'] %}
  {% set mgmt_nw = 'mgmt0' %}
{% else %}
  {% set mgmt_nw = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] %}
{% endif %}
# Configure halond
Update Halon config file:
  file.managed:
    - name: /etc/sysconfig/halond
    - contents:
      - HALOND_LISTEN={{ grains["ip4_interfaces"][mgmt_nw][0] }}:9070
      - HALOND_STATION_OPTIONS="--rs-lease 4000000"
    - user: root
    - group: root

