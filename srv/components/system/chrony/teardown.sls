Disable chronyd:
  service.dead:
    - name: chronyd
    - enable: false

Remove chrony package:
  pkg.removed:
    - name: chrony

Remove chrony configutations:
  file.absent:
    - name: /etc/chrony.conf
...
