include:
  - components.misc_pkgs.rsyslog.install

Start rsyslog:
  service.running:
    - name: rsyslog.service
    - enable: True
    - require:
      - Install rsyslog service
