# general settings
Logrotate config file - Generic:
  file.managed:
    - name: /etc/logrotate.conf
    - source: salt://components/system/logrotate/files/etc/logrotate.conf

# logrotate.d
Create logrotate.d with specific component settings:
  file.recurse:
  - name: /etc/logrotate.d
  - source: salt://components/system/logrotate/files/etc/logrotate.d
  - keep_source: True
  - dir_mode: 0750
  - file_mode: 0640
  - user: root
  - group: root
  - clean: False
  - include_empty: True
