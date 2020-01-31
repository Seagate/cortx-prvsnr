include:
  - components.misc_pkgs.rsyslog.install

Ensure rsyslog started:
  service.running:
    - name: rsyslog.service
    - enable: True
    - require:
      - Install rsyslog service
