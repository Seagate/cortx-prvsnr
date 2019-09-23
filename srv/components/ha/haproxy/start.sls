Ensure HAProxy running:
  service.running:
    - name: haproxy.service

Ensure rsyslog running:
  service.running:
    - name: rsyslog.service
