include:
  - components.misc_pkgs.statsd.stop

Remove statsd:
  pkg.purged:
    - pkgs:
      - statsd

Remove statsd configuration:
  file.absent:
    - name: /etc/statsd