include:
  - components.system.prepare


Rescan SCSI:
  module.run:
    - scsi.rescan_all:
      - host: 0
