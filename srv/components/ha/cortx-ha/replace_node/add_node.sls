Run cortx-ha add_node:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:add_node')
    - onlyif: test -x /opt/seagate/cortx/ha/conf/setup.yaml
