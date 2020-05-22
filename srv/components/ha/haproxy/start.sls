Ensure HAProxy running:
  service.running:
    - name: haproxy.service
    - enable: True

include:
  - components.misc_pkgs.rsyslog.start
