include:
  - components.misc_pkgs.rsyslog.stop

Remove rsyslog service:
  pkg.purged:
    - name: rsyslog
