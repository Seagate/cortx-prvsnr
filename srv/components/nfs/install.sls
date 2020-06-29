Install prereq packages for NFS:
  pkg.installed:
    - pkgs:
      - jemalloc
      - krb5-devel
      - libini_config-devel
      - krb5-server
      - krb5-libs
      - nfs-utils
      - rpcbind libblkid
#TODO: confirm the library name
      - libevhttp #TBD

{% for path in [
  "/usr/lib64/libcap.so",
  "/usr/lib64/libjemalloc.so",
  "/usr/lib64/libnfsidmap.so",
  "/usr/lib64/libblkid.so"
] %}
{{ path }}.1:
  file.symlink:
    - target: {{ path }}
    - force: True
    - makedirs: True
{% endfor %}

Install NFS Ganesha:
  pkg.installed:
#TODO: Make sure it's installed from GitHub
    - name: nfs-ganesha

Install NFS packages:
  pkg.installed:
    - pkgs:
      cortx-dsal
      cortx-dsal-devel
      cortx-fs
      cortx-fs-devel
      cortx-fs-ganesha
      cortx-fs-ganesha-test
      cortx-nsal
      cortx-nsal-devel
      cortx-utils
      cortx-utils-devel