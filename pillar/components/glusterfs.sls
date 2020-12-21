glusterfs:
  in_docker: false
  network_type: mgmt  # mgmt/data
  volumes:
    - name: volume_prvsnr_data
      export_dir: /srv/glusterfs/volume_prvsnr_data
      mount_dir: /var/lib/seagate/cortx/provisioner/shared
    - name: volume_salt_cache_jobs
      export_dir: /srv/glusterfs/volume_salt_cache_jobs
      mount_dir: /var/cache/salt/master/jobs
