Restart HAProxy:
  service.running:
    - name: haproxy

Start slapd:
  service.running:
    - name: slapd

Restart s3authserver:
  service.running:
    - name: s3authserver
    - require:
      - Start slapd
