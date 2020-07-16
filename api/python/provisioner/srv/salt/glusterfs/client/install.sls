include:
  - ..install

glusterfs_client_installed:
  pkg.installed:
    - pkgs:
      # TODO IMPROVE EOS-9581 would be different for Debian/Ubuntu
      - glusterfs-fuse
    - require:
      - glusterfs_repo_is_installed
