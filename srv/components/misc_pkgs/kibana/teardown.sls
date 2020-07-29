include:
  - components.misc_pkgs.kibana.stop

Remove kibana:
  pkg.purged:
    - name: kibana-oss

Remove kibana config:
  file.absent:
    - names:
      - /etc/kibana
      - /var/lib/kibana

Delete kibana checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.kibana
