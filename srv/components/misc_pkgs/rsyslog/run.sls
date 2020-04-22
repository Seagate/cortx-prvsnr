rsyslog_running:
  service.running:
    - name: rsyslog.service
    - enable: True
