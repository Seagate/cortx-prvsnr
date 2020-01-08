include:
  - components.misc.rsyslog.start

Ensure HAProxy running:
  service.running:
    - name: haproxy.service
    - require:
      - service: Ensure rsyslog running
