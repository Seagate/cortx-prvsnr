include:
  - components.misc_pkgs.elasticsearch

Update config:
  file.managed:
    - name: /etc/statsd/config.js
    - source: salt://components/misc/statsd/files/config.js
    - require:
      - Install elasticsearch
