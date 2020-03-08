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
...
