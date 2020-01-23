{% import_yaml 'components/defaults.yaml' as defaults -%}

# logrotate.d
Setup logrotate policy for halon decision log:
  file.managed:
  - name: /etc/logrotate.d/halon
  - source: salt://components/halon/files/etc/logrotate.d/halon
  - keep_source: False

# Configure halond
Update Halon config file:
  file.managed:
    - name: /etc/sysconfig/halond
    - contents:
      - HALOND_LISTEN={{ grains["ip4_interfaces"]['mgmt0'][0] }}:9070
      - HALOND_STATION_OPTIONS="--rs-lease 4000000"
    - user: root
    - group: root

