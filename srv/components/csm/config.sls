include:
  - components.misc_pkgs.elasticsearch

Update config:
  file.managed:
    - name: /etc/statsd/config.js
    - source: salt://components/csm/files/config.js
    - require:
      - Install elasticsearch

#CSM Configuration and Initialization
Initialize CSM setup:
  cmd.run:
    - name: csm_setup init -f
