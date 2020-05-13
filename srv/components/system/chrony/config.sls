Setup time zone:
  timezone.system:
    - name: {{ pillar['system']['ntp']['timezone'] }}

Setup NTP config file:
  file.managed:
    - name: /etc/chrony.conf
    - source: salt://components/system/chrony/files/chrony.conf
    - makedirs: True
    - keep_source: True
    - template: jinja
