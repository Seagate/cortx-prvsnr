Add common config - system information to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv put system_information/operating_system "$(cat /etc/system-release)"
        /opt/seagate/cortx/hare/bin/consul kv put system_information/kernel_version {{ grains['kernelrelease'] }}
        /opt/seagate/cortx/hare/bin/consul kv put system_information/product {{ pillar['cluster']['type'] }}
        /opt/seagate/cortx/hare/bin/consul kv put system_information/site_id 001
        /opt/seagate/cortx/hare/bin/consul kv put system_information/rack_id 001
        /opt/seagate/cortx/hare/bin/consul kv put system_information/cluster_id {{ grains['cluster_id'] }}
        /opt/seagate/cortx/hare/bin/consul kv put system_information/{{ grains['id'] }}/node_id {{ grains['node_id'] }}
        /opt/seagate/cortx/hare/bin/consul kv put system_information/syslog_host {{ pillar['rsyslog']['host'] }}
        /opt/seagate/cortx/hare/bin/consul kv put system_information/syslog_port {{ pillar['rsyslog']['port'] }}
        /opt/seagate/cortx/hare/bin/consul kv put system_information/healthmappath {{ pillar['sspl']['health_map_path'] + '/' + pillar['sspl']['health_map_file'] }}

Add common config - rabbitmq cluster to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv put rabbitmq/cluster_nodes {{ pillar['rabbitmq']['cluster_nodes'] }}
        /opt/seagate/cortx/hare/bin/consul kv put rabbitmq/erlang_cookie {{ pillar['rabbitmq']['erlang_cookie'] }}

Add common config - BMC to Consul:
  cmd.run:
    - name: |
{% for node in pillar['cluster']['node_list'] %}
        /opt/seagate/cortx/hare/bin/consul kv put bmc/{{ node }}/ip {{ pillar['cluster'][node]['bmc']['ip'] }}
        /opt/seagate/cortx/hare/bin/consul kv put bmc/{{ node }}/user {{ pillar['cluster'][node]['bmc']['user'] }}
        /opt/seagate/cortx/hare/bin/consul kv put bmc/{{ node }}/secret {{ pillar['cluster'][node]['bmc']['secret'] }}
{% endfor %}

Add common config - storage enclosure to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv put storage_enclosure/controller/primary_mc/ip {{ pillar['storage_enclosure']['controller']['primary_mc']['ip'] }}
        /opt/seagate/cortx/hare/bin/consul kv put storage_enclosure/controller/primary_mc/port {{ pillar['storage_enclosure']['controller']['primary_mc']['port'] }}
        /opt/seagate/cortx/hare/bin/consul kv put storage_enclosure/controller/secondary_mc/ip {{ pillar['storage_enclosure']['controller']['secondary_mc']['ip'] }}
        /opt/seagate/cortx/hare/bin/consul kv put storage_enclosure/controller/secondary_mc/port {{ pillar['storage_enclosure']['controller']['secondary_mc']['port'] }}
        /opt/seagate/cortx/hare/bin/consul kv put storage_enclosure/controller/user {{ pillar['storage_enclosure']['controller']['user'] }}
        /opt/seagate/cortx/hare/bin/consul kv put storage_enclosure/controller/password {{ pillar['storage_enclosure']['controller']['secret'] }}
