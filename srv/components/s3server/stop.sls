
stop s3authserver:
  service.dead:
    - name: s3authserver

stop haproxy:
  service.dead:
    - name: haproxy
    - watch:
      - service: s3authserver

stop slapd:
  service.dead:
    - name: slapd
