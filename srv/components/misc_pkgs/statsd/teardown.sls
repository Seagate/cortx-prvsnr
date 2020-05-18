include:
  - components.misc_pkgs.statsd.stop

Remove statsd:
  pkg.purged:
    - pkgs:
      - statsd
      - stats_utils

Remove statsd configuration:
  file.absent:
    - name: /etc/statsd

Remove /opt/statsd-utils:
  file.absent:
    - name: /opt/statsd-utils
