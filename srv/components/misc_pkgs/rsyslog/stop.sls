Ensure rsyslog stopped:
  service.dead:
    - name: rsyslog.service
    - enable: False
    - init_delay: 2
