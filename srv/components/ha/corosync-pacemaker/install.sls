Create ha user:
  user.present:
    - name: hacluster
    - password: {{ pillar['corosync-pacemaker']['password'] }}
    - gid: haclient
    - allow_uid_change: True
    - allow_gid_change: True
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

Install runtime libraries:
  pkg.installed:
    - pkgs:
      - corosync
      - pacemaker
      - pcs
