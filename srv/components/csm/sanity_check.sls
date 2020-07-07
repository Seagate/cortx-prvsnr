Stage - Test CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/csm/conf/setup.yaml', 'csm:test')
