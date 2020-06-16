include:
  - components.sspl.install
  - .commons
  - components.sspl.health_view.prepare
  - components.sspl.health_view.config

Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:post_install')
    - require:
      - Install eos-sspl packages

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:config')
    - require:
      - Stage - Post Install SSPL
      - Add common config - system information to Consul
      - Add common config - rabbitmq cluster to Consul
      - Add common config - BMC to Consul
      - Add common config - storage enclosure to Consul
    - order: 5

Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:init')
    - require:
      - Copy setup.yaml to /opt/seagate/health_view/conf
      - Run Resource Health View
      - Stage - Configure SSPL
    - order: 10
