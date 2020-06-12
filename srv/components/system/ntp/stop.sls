ntp_stop:
  service.dead:
    - name: ntpd
