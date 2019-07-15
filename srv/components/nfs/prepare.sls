{% import_yaml 'components/defaults.yaml' as defaults %}

Add nfs_prereqs yum repo:
  pkgrepo.managed:
    - name: {{ defaults.nfs.uploads_repo.id }}
    - enabled: True
    - humanname: nfs_uploads
    - baseurl: {{ defaults.nfs.uploads_repo.url }}
    - gpgcheck: 0

# Add nfs yum repo:
#   pkgrepo.managed:
#     - name: {{ defaults.nfs.repo.id }}
#     - enabled: True
#     - humanname: nfs
#     - baseurl: {{ defaults.nfs.repo.url }}
#     - gpgcheck: 0

Copy kvsns.ini file:
  file.managed:
    - name: /etc/kvsns.d/kvsns.ini
    - source: salt://components/nfs/files/etc/kvsns.d/kvsns.ini
    - makedirs: True

Copy ganesha.conf file:
  file.managed:
    - name: /etc/ganesha/ganesha.conf
    - source: salt://components/nfs/files/etc/ganesha/ganesha.conf
    - makedirs: True
