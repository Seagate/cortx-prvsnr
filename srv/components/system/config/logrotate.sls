# Setup log rotation policies

# Install logrotate
logrotate_packages:
  pkg.installed:
    - name: logrotate

# general settings
generic_logrotate_config:
  file.managed:
    - name: /etc/logrotate.conf
    - source: salt://components/system/files/etc/logrotate.conf

# logrotate.d
logrotate_directory:
  file.recurse:
  - name: /etc/logrotate.d
  - source: salt://components/system/files/etc/logrotate.d
  - keep_source: True
  - dir_mode: 0750
  - file_mode: 0640
  - user: root
  - group: root
  - clean: False
  - include_empty: True
