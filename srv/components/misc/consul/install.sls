include:
  - components.misc.consul.prepare

Consul installed:
  archive.extracted:
    - name: /opt/consul/bin
    - source: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_linux_amd64.zip
    - source_hash: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_SHA256SUMS
    - source_hash_name: consul_1.6.2_linux_amd64.zip
    - enforce_toplevel: False
    - keep_source: True
    - clean: False
    - trim_output: True
    - user: consul
    - group: consul
    - if_missing: /opt/consul/bin/consul
    - require:
      - user: Create Consul user

Update Consul executable with required permissions:
  file.managed:
    - name: /opt/consul/bin/consul
    - user: consul
    - group: consul
    - mode: 755
    - require:
      - user: Create Consul user
