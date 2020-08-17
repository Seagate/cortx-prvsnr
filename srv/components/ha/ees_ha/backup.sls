Stage - Backup files for LDR1-HA:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ldr1.yaml', 'ldr1-ha:backup')
