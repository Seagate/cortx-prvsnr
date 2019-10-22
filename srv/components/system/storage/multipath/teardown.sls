Stop and disable multipath service:
  service.dead:
    - name: multipathd.service
    - enable: false

Remove multipath service:
  pkg.purged:
    - name: device-mapper-multipath

Remove multipath config:
  file.absent:
    - name: /etc/multipath.conf
