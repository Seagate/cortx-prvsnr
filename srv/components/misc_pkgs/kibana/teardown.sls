include:
  - components.misc_pkgs.kibana.stop

Remove kibana:
  pkg.purged:
    - name: kibana

Remove kibana config:
  file.absent:
    - names:
      - /etc/kibana
      - /var/lib/kibana
