Start sldapd service:
  service.running:
    - name: slapd
    - enable: True
