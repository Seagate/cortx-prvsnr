#CSM Configuration and Initialization                                                                     
Stage - Post Install CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:post_install')
 
Stage - Config CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:config')
    - require:
      - Stage - Post Install CSM
                                                                                                          
Add csm user to certs group:
  group.present:
    - name: certs
    - addusers:
      - csm
    - require:
      - Stage - Config CSM
                                                                                                          
Stage - Init CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:init')
    - require:
      - Add csm user to certs group
