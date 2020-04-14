Disable ntpd:
  service.dead:
    - name: ntpd
    - enable: false
  
Remove_ntp_package:
  pkg.removed:
    - name: ntp

Remove ntp configutations:
  file.absent:
    - name: /etc/ntp

Delete ntp checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.ntp