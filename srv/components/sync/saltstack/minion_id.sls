# This file is intended to be used with salt-ssh.
# Thus, roles can be defined as custom grains being utilized here.
Set minion_id based on role:
  file.managed:
    - name: /etc/salt/minion_id
