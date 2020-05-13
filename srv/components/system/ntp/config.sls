Setup time zone:
  timezone.system:
    - name: {{ pillar['system']['ntp']['timezone'] }}

Update HW clock sync:
  file.managed:
    - name: /etc/sysconfig/ntpdate
    - source: salt://components/system/ntp/files/ntpdate.conf
    - makedirs: True
    - keep_source: True

Setup NTP config file:
  file.managed:
    - name: /etc/ntp.conf
    - source: salt://components/system/ntp/files/ntp.conf
    - makedirs: True
    - keep_source: True
    - template: jinja
