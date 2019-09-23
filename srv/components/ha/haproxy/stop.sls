Ensure rsyslog stopped:
  service.dead:
    - name: rsyslog.service

Ensure HAProxy stopped:
  service.dead:
    - name: haproxy.service
