Stage - Backup files for S3:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:backup')
