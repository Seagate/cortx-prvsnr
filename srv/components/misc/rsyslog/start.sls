Ensure rsyslog running:
  service.running:
    - name: rsyslog.service
    - enable: True
