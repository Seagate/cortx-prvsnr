include:
  - components.misc.statsd.stop

Remove statsd:
  pkg.purged:
    - pkgs:
      - statsd
      - python-statsd

Remove config:
  file.absent:
    - name: /etc/statsd/config.js
