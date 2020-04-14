include:
  - components.misc_pkgs.rsyslog.stop

Remove rsyslog service:
  pkg.purged:
    - name: rsyslog

Delete rsyslog checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.rsyslog