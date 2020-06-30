Remove NFS packages:
  pkg.removed:
    - pkgs:
      - cortx-dsal
      - cortx-dsal-devel
      - cortx-fs
      - cortx-fs-devel
      - cortx-fs-ganesha
      - cortx-fs-ganesha-test
      - cortx-nsal
      - cortx-nsal-devel
      - cortx-utils
      - cortx-utils-devel
    - disableexcludes: main

Remove NFS Ganesha:
  pkg.removed:
    - name: nfs-ganesha

Remove prereq packages for NFS:
  pkg.removed:
    - pkgs:
      - jemalloc
      - krb5-devel
      - libini_config-devel
      - krb5-server
      - nfs-utils
      - rpcbind
      - libevhtp
# Removing libblkid & krb5-libs removes systemd and
# other important system libraries, don't remove them.
      #- libblkid
      #- krb5-libs

Delete nfs checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.nfs
