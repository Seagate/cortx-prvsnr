include:
  - components.misc.rsyslog.stop

Ensure HAProxy stopped:
  service.dead:
    - name: haproxy.service
    - require:
      - service: Ensure rsyslog dead
