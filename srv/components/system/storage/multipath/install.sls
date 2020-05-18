include:
  - components.system.storage.multipath.prepare

Install multipath:
  pkg.installed:
    - name: device-mapper-multipath
    - require:
      - Rescan SCSI
