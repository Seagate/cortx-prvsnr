Run cortx-ha refresh_context:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:refresh_config')
    - onlyif: test -x /opt/seagate/cortx/ha/conf/setup.yaml