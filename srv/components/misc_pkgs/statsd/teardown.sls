include:
  - components.misc_pkgs.statsd.stop

Remove statsd:
  pkg.purged:
    - pkgs:
      - statsd
