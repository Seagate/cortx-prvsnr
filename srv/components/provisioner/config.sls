# TODO IMPROVE salt configs might go here as well
include:
  - components.misc_pkgs.rsyslog

provisioner_rsyslog_conf_updated:
  file.managed:
    - name: /etc/rsyslog.d/prvsnrfwd.conf
    - source: salt://components/provisioner/files/prvsnrfwd.conf
    - makedirs: True
    - watch_in:
      - service: Start rsyslog
