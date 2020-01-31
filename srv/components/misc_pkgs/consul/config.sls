include:
  - components.misc_pkgs.consul.prepare
  - components.misc_pkgs.consul.install

Set consul in bash_profile:
  file.blockreplace:
    - name: ~/.bashrc
    - marker_start: '# DO NOT EDIT: Consul binaries'
    - marker_end: '# DO NOT EDIT: End'
    - content: 'export PATH=/opt/consul:$PATH'
    - append_if_not_found: True
    - append_newline: True
    - backup: False
    - require:
      - Consul installed

Source bash_profile for nodejs addition:
  cmd.run:
    - name: source ~/.bashrc
    - require: 
      - Set consul in bash_profile

Reload service daemons for consul-agent.service:
  cmd.run:
    - name: systemctl daemon-reload
    - require:
      - file: Create Consul Agent Service
      - Consul installed
