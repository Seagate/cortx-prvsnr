Stage - Refresh config for SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/sspl/conf/setup.yaml', 'sspl:refresh_config')
