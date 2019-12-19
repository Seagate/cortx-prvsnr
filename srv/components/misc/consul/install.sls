Extract Consul:
  archive.extracted:
    - name: /opt/consul
    - source: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_linux_amd64.zip
    - source_hash: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_SHA256SUMS
    - source_hash_name: consul_1.6.2_linux_amd64.zip
    - enforce_toplevel: False
    - keep_source: True
    - clean: True
    - trim_output: True
