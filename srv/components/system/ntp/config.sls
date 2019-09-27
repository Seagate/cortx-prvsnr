setup_ntp_config:
  file.managed:
    - name: /etc/ntp.conf
    - source: salt://components/system/ntp/files/ntp.conf
    - makedirs: True
    - keep_source: True
    - template: jinja
...