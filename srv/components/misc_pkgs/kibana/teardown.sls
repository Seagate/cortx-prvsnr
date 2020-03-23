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

Delete kibana checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.kibana
