haproxy:
  pkg.installed: []
  service.running:
    - enable: True

rsyslog:
  service.running:
    - enable: True
