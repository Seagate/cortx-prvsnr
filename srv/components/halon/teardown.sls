disable_halon_service:
  service.dead:
    - name: halond
    - enable: false

delete_halon_conf:
  file.managed:
    - name: /etc/sysconfig/halond
    - contents:
      - HALOND_LISTEN={{ defaults.halon.rc_listen.ip }}:{{ defaults.halon.rc_listen.port }}
      - HALOND_STATION_OPTIONS="--rs-lease 4000000"
    - user: root
    - group: root
