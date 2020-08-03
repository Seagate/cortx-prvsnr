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
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.multipath

Remove multipath conf file:
  file.absent:
    - name: /etc/multipath.conf

{% if salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.cc'.format(grains['id'])) %}
Delete cross-connect checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.cc
{% endif %}
