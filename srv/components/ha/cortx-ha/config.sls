include:
  - components.ha.cortx-ha.install

Run cortx-ha post_install:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:post_install')
    - require:
      - Install cortx-ha
    
Run cortx-ha config:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:config')
    - require:
      - Install cortx-ha

Run cortx-ha init:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:init')
    - require:
      - Install cortx-ha