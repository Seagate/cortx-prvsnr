ntp_service_disable:
  service.dead:
    - name: ntpd
    - enable: false
  
remove_ntp_package:
  pkg.removed:
    - name: ntp
...
