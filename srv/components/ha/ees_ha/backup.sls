Stage - Backup files for EES-HA:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ees-ha:backup')
