Create Consul user:
  user.present:
    - name: consul
    - home: /etc/consul.d
    - system: True
    - shell: /bin/false

Create Consul bin directory:
  file.directory:
    - name: /opt/consul/bin
    - makedirs: True
    - dir_mode: 755
    - file_mode: 644
    - user: consul
    - group: consul
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Consul user

Create Consul data directory:
  file.directory:
    - name: /opt/consul/data
    - makedirs: True
    - dir_mode: 755
    - file_mode: 644
    - user: consul
    - group: consul
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Consul user

Create Consul config directory:
  file.directory:
    - name: /etc/consul.d
    - makedirs: True
    - dir_mode: 750
    - file_mode: 640
    - user: consul
    - group: consul
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Consul user

Create Consul server config file:
  file.managed:
    - name: /etc/consul.d/consul_server.json
    - source: salt://components/misc_pkgs/consul/files/consul_server.json.j2
    - mode: 640
    - template: jinja
    - user: consul
    - group: consul
    - require:
      - user: Create Consul user

Create Consul Agent Service:
  file.managed:
    - name: /etc/systemd/system/consul.service
    - source: salt://components/misc_pkgs/consul/files/consul.service
    - makedirs: True
    - mode: 640
    - template: jinja
