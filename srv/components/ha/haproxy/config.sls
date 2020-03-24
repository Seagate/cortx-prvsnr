Add haproxy user to certs group:
  group.present:
    - name: certs
    - addusers:
      - haproxy

Setup HAProxy config:
  file.managed:
    - name: /etc/haproxy/haproxy.cfg
    - source: salt://components/ha/haproxy/files/haproxy.cfg
    - makedirs: True
    - keep_source: False
    - template: jinja

Setup haproxy 503 error code to http file:
  file.managed:
    - name: /etc/haproxy/errors/503.http
    - source: salt://components/ha/haproxy/files/503.http
    - makedirs: True
    - keep_source: False

Setup logrotate config for haproxy:
  file.managed:
    - name: /etc/logrotate.d/haproxy
    - source: salt://components/ha/haproxy/files/logrotate/haproxy
    - makedirs: True
    - keep_source: False

Setup logrotate cron for haproxy to run hourly:
  file.managed:
    - name: /etc/cron.hourly/logrotate
    - source: salt://components/ha/haproxy/files/logrotate/logrotate
    - keep_source: False
    - makedirs: True

Setup haproxy config to enable logs:
  file.managed:
    - name: /etc/rsyslog.d/haproxy.conf
    - source: salt://components/ha/haproxy/files/rsyslog.d/haproxy.conf
    - makedirs: True
    - keep_source: False

include:
  - components.misc_pkgs.rsyslog.start