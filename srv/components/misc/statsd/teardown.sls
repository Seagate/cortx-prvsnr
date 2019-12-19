Remove statsd:
  pkg.purged:
    - name: statsd

Remove config:
  file.absent:
    - name: /etc/statsd/config.js
