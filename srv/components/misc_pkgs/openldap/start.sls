Start sldapd service:
  service.running:
    - name: slapd
    - enable: True

Restart slapd service:
  module.run:
    - service.restart:
      - name: slapd
