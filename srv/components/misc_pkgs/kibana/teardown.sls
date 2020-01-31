include:
  - components.misc_pkgs.kibana.stop

Remove kibana:
  pkg.purged:
    - name: kibana

Remove kibana config:
  file.absent:
    - name: /etc/kibana/kibana.yml
