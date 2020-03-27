include:
  - .stop

Remove scsi-network-relay driver:
  pkg.purged:
    - name: scsi-network-relay

Remove config file:
  file.absent:
    - name: /etc/scsi-network-relay.conf
