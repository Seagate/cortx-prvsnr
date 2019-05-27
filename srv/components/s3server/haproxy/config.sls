Restart HAProxy:
  service.running:
    - name: haproxy.service

Restart Rsyslog:
  service.running:
    - name: rsyslog.service

Setup haproxy config:
  file.managed:
    - name: /etc/haproxy/haproxy.cfg
    - source: salt://components/s3server/haproxy/files/haproxy.cfg
    - makedirs: True
    - keep_source: False
    - template: jinja
    - watch_in:
      - service: Restart HAProxy

Setup haproxy 503 error code to http file:
  file.managed:
    - name: /etc/haproxy/errors/503.http
    - source: salt://components/s3server/haproxy/files/503.http
    - makedirs: True
    - keep_source: False

Setup logrotate config for haproxy:
  file.managed:
    - name: /etc/logrotate.d/haproxy
    - source: salt://components/s3server/haproxy/files/logrotate/haproxy
    - makedirs: True
    - keep_source: False

Setup logrotate config for haproxy to run hourly:
  file.managed:
    - name: /etc/cron.hourly/logrotate
    - source: salt://components/s3server/haproxy/files/logrotate/logrotate
    - keep_source: False
    - makedirs: True

Setup haproxy config to enable logs:
  file.managed:
    - name: /etc/rsyslog.d/haproxy.conf
    - source: salt://components/s3server/haproxy/files/rsyslog.d/haproxy.conf
    - makedirs: True
    - keep_source: False
    - watch_in:
      - service: Restart Rsyslog
