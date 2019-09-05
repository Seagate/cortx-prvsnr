Install multipath:
  pkg.installed:
    - name: device-mapper-multipath

Start multipath service:
  service.running:
    - name: multipathd.service
    - enable: True