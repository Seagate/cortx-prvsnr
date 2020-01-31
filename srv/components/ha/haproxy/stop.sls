include:
  - components.misc_pkgs.rsyslog.stop

Ensure HAProxy stopped:
  service.dead:
    - name: haproxy.service
