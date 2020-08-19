Stage - Backup files for LDR-R1-HA:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup-ldr-r1.yaml', 'ldr-r1-ha:backup')
