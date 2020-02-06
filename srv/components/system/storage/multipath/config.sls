{%
  if salt['file.file_exists']('/etc/multipath.conf')
  and not salt['file.file_exists']('/etc/multipath.conf.org') 
%}
Backup multipath config:
  file.copy:
    - name: /etc/multipath.conf.org
    - source: /etc/multipath.conf
    - force: True
    - makedirs: True
{% endif %}

Copy multipath config:
  file.copy:
    - name: /etc/multipath.conf
    - source: salt://components/system/storage/multipath/files/multipath.conf
    - force: True
    - makedirs: True

Restart multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config

# End Setup multipath

Rescan SCSI:
  module.run:
    - scsi.rescan_all:
      - host: 0
