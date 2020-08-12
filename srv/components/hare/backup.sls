Stage - Backup files for HARE:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/hare/conf/setup.yaml', 'hare:backup')
