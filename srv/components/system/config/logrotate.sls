# Setup log rotation policies

# Install logrotate
logrotate_packages:
  pkg.installed:
    - name: logrotate

# general settings
generic:
  file.managed:
    - name: /etc/logrotate.conf
    - source: salt://components/system/config/files/etc/logrotate.conf

# logrotate.d
logrotate_directory:
  file.recurse:
  - name: /etc/logrotate.d
  - source: salt://components/config/files/etc/logrotate.d
  - keep_source: True
  - dir_mode: 0750
  - file_mode: 0640
  - user: root
  - group: root
  - clean: False
  - include_empty: True


{% if salt['grains.get']('host').startswith('cmu') %}
# logrotate settings for cmu
logrotate_directory_cmu:
  file.recurse:
  - name: /etc/logrotate.d
  - source: salt://cmu/files/etc/logrotate.d
  - keep_source: True
  - dir_mode: 0750
  - file_mode: 0640
  - user: root
  - group: root
  - clean: False
  - include_empty: True
  - require:
    - file: logrotate_directory

{% elif salt['grains.get']('host').startswith('qb') %}
# logrotate settings for quadblade
logrotate_directory_quadblade:
  file.recurse:
  - name: /etc/logrotate.d
  - source: salt://quadblade/files/etc/logrotate.d
  - keep_source: True
  - dir_mode: 0750
  - file_mode: 0640
  - user: root
  - group: root
  - clean: False
  - include_empty: True
  - require:
    - file: logrotate_directory

{% else %}
# logrotate settings for ssu
logrotate_directory_ssu:
  file.recurse:
  - name: /etc/logrotate.d
  - source: salt://ssu/files/etc/logrotate.d
  - keep_source: True
  - dir_mode: 0750
  - file_mode: 0640
  - user: root
  - group: root
  - clean: False
  - include_empty: True
  - require:
    - file: logrotate_directory

{% endif %}
