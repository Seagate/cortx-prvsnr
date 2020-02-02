include:
  - components.misc_pkgs.consul.stop

Remove Consul:
  file.absent:
    - name: /opt/consul

Remove consul from bash_profile:
  file.blockreplace:
    - name: ~/.bashrc
    - marker_start: '# DO NOT EDIT: Consul binaries'
    - marker_end: '# DO NOT EDIT: End'
    - content: ''

Source bash_profile for consul cleanup:
  cmd.run:
    - name: source ~/.bashrc

Remove Consul data directory:
  file.absent:
    - name: /opt/consul/data
    
Remove Consul config directory:
  file.absent:
    - name: /etc/consul.d
    
Remove Consul agent config file:
  file.absent:
    - name: /etc/consul.d/consul.json

Remove Consul server config file:
  file.absent:
    - name: /etc/consul.d/consul_server.json
    - source: salt://components/misc_pkgs/consul/files/consul_server.json
    - mode: 640
    - template: jinja

Remove Consul Agent Service:
  file.absent:
    - name: /etc/systemd/system/consul.service
    - source: salt://components/misc_pkgs/consul/files/consul.service
    - makedirs: True
    - mode: 644

Reload service daemons post consul-agent.service removal:
  cmd.run:
    - name: systemctl daemon-reload

Remove Consul user:
  user.absent:
    - name: consul
