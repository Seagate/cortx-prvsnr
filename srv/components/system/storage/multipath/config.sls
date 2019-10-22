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
    - source: /usr/share/doc/device-mapper-multipath-0.4.9/multipath.conf
    - force: True
    - makedirs: True

Delay multipath start:
  cmd.run:
    - name: sleep 1

Restart multipath service:
  service.running:
    - name: multipathd.service
    - enable: True
    - watch:
      - file: Copy multipath config
# End Setup multipath
