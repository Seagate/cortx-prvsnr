include:
  - component.misc.rsyslog.stop

Ensure rsyslog disable:
  service.disabled:
    - name: rsyslog.service

Purge rsyslog:
  pkg.purged:
    - name: rsyslog
