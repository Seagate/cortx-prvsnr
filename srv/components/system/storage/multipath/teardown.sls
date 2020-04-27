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

Delete multipath checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.multipath

Remove multipath conf file:
  file.absent:
    - name: /etc/multipath.conf
