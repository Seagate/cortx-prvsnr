# TODO IMPROVE salt configs might go here as well

{% set rsyslog_running = salt['service.status']('rsyslog') %}

{% if rsyslog_running %}
include:
  - components.misc_pkgs.rsyslog.run
{% endif %}

provisioner_rsyslog_conf_updated:
  file.managed:
    - name: /etc/rsyslog.d/2-prvsnrfwd.conf
    - source: salt://components/provisioner/files/prvsnrfwd.conf
    - makedirs: True
{% if rsyslog_running %}
    # restart rsyslog only if it is already running
    - watch_in:
      - service: rsyslog_running
{% endif %}
