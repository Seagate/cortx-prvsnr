include:
  - .sspl

Delete common config - system information to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv delete system_information/operating_system
        /opt/seagate/eos/hare/bin/consul kv delete system_information/kernel_version
        /opt/seagate/eos/hare/bin/consul kv delete system_information/product
        /opt/seagate/eos/hare/bin/consul kv delete system_information/site_id
        /opt/seagate/eos/hare/bin/consul kv delete system_information/rack_id
        /opt/seagate/eos/hare/bin/consul kv delete system_information/cluster_id
        /opt/seagate/eos/hare/bin/consul kv delete system_information/{{ grains['id'] }}/node_id
        /opt/seagate/eos/hare/bin/consul kv delete system_information/syslog_host
        /opt/seagate/eos/hare/bin/consul kv delete system_information/syslog_port
        /opt/seagate/eos/hare/bin/consul kv delete system_information/healthmappath
    - require:
      - Delete sspl checkpoint flag

Delete common config - rabbitmq cluster to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv delete rabbitmq/cluster_nodes
        /opt/seagate/eos/hare/bin/consul kv delete rabbitmq/erlang_cookie
    - require:
      - Delete sspl checkpoint flag

Delete common config - BMC to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv delete bmc/srvnode-1/ip
        /opt/seagate/eos/hare/bin/consul kv delete bmc/srvnode-1/user
        /opt/seagate/eos/hare/bin/consul kv delete bmc/srvnode-1/secret['secret']
        /opt/seagate/eos/hare/bin/consul kv delete bmc/srvnode-2/ip
        /opt/seagate/eos/hare/bin/consul kv delete bmc/srvnode-2/user
        /opt/seagate/eos/hare/bin/consul kv delete bmc/srvnode-2/secret
    - require:
      - Delete sspl checkpoint flag

Delete common config - storage enclosure to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv delete storage_enclosure/controller/primary_mc/ip
        /opt/seagate/eos/hare/bin/consul kv delete storage_enclosure/controller/primary_mc/port
        /opt/seagate/eos/hare/bin/consul kv delete storage_enclosure/controller/secondary_mc/ip
        /opt/seagate/eos/hare/bin/consul kv delete storage_enclosure/controller/secondary_mc/port
        /opt/seagate/eos/hare/bin/consul kv delete storage_enclosure/controller/user
        /opt/seagate/eos/hare/bin/consul kv delete storage_enclosure/controller/password
    - require:
      - Delete sspl checkpoint flag
