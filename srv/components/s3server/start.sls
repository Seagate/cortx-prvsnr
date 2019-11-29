Restart HAProxy:
  service.running:
    - name: haproxy

Restart slapd:
  service.running:
    - name: slapd

Start s3authserver:
  service.running:
    - name: s3authserver
    - enable: True
    - require:
      - Restart slapd
