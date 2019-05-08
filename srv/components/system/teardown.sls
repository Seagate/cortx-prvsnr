install_base_packages:
  pkg.absent:
    - pkgs:
      - python2-pip
      # - vi-enhanced
      # - tmux

# Log rotate teardown start
# logrotate.d
remove_logrotate_directory:
  file.absent:
    - name: /etc/logrotate.d
    - source: salt://components/system/files/etc/logrotate.d
    - keep_source: True
    - dir_mode: 0750
    - file_mode: 0640
    - user: root
    - group: root
    - clean: False
    - include_empty: True

# general settings
remove_generic_logrotate_config:
  file.absent:
    - name: /etc/logrotate.conf
    - source: salt://components/system/files/etc/logrotate.conf


# Remove logrotate
logrotate_packages:
  pkg.installed:
    - name: logrotate
