#include:
#  - ..install

glusterfs_server_installed:
  pkg.installed:
    - pkgs:
      - glusterfs-server
#    - require:
#      - glusterfs_repo_is_installed

glusterfs_daemon_running:
  service.running:
    - name: glusterd.service
#    - require:
#        - glusterfs_server_installed
