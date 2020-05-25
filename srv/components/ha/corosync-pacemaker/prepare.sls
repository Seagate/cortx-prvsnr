Create ha user:
  user.present:
    - name: {{ pillar['corosync-pacemaker']['user'] }}
    - password: {{ salt['lyveutil.decrypt'](pillar['corosync-pacemaker']['secret'], 'corosync-pacemaker') }}
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

Disable SSL:
  file.managed:
    - name: /etc/python/cert-verification.cfg
    - contents: |
        [https]
        verify=disable
