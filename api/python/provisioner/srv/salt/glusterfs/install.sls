#glusterfs_repo_is_installed:
#  pkg.installed:
#    - pkgs:
#      - centos-release-gluster7

# centos-release-gluster7 not available for redhat hence adding repo manually
glusterfs_repo_is_installed:
  pkgrepo.managed:
    - name: glusterfs
    - humanname: glusterfs-7
    - baseurl: http://mirror.centos.org/centos/7/storage/x86_64/gluster-7/
    - gpgcheck: 0
    - enbaled: 1