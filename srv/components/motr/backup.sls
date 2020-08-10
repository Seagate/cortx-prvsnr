Stage - Backup files for Motr:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/motr/conf/setup.yaml', 'core:backup')
