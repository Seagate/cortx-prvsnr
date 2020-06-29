# This file is intended to be used with salt-ssh.
# Thus, roles can be defined as custom grains being utilized here.
Set minion_id based on role:
  file.managed:
    - name: /etc/salt/minion_id
    - contents_grains: id
    - makedirs: True
    - create: True
    - replace: False
    - user: root
    - group: root
    - mode: 644
    - contents_newline: True

Set grains:
  file.managed:
    - name: /etc/salt/grains
    - source: salt://components/sync/salt/files/grains
    - template: jinja
    - makedirs: True
    - create: True
    - replace: False
    - user: root
    - group: root
    - mode: 644
    - contents_newline: True
