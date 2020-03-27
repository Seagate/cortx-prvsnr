Copy the config file:
  file.managed:
    - name: /etc/scsi-network-relay.conf
    - source: salt://components/system/inband/files/scsi-network-relay.conf
    - template: jinja
    - replace: True
    - keep_source: False
    - makedirs: True
    - create: True
