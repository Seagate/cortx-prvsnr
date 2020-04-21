{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Add common config - system information to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv put system_information/operating_system "{{ grains['lsb_distrib_codename'] }}"
        /opt/seagate/eos/hare/bin/consul kv put system_information/kernel_version {{ grains['kernelrelease'] }}
        /opt/seagate/eos/hare/bin/consul kv put system_information/product {{ pillar['cluster']['type'] }}
        /opt/seagate/eos/hare/bin/consul kv put system_information/site_id 001
        /opt/seagate/eos/hare/bin/consul kv put system_information/rack_id 001
        /opt/seagate/eos/hare/bin/consul kv put system_information/cluster_id {{ grains['cluster_id'] }}
        /opt/seagate/eos/hare/bin/consul kv put system_information/node_id {{ grains['node_id'] }}
        /opt/seagate/eos/hare/bin/consul kv put system_information/syslog_host {{ pillar['rsyslog']['host'] }}
        /opt/seagate/eos/hare/bin/consul kv put system_information/syslog_port {{ pillar['rsyslog']['port'] }}

Add common config - rabbitmq cluster to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv put rabbitmq/cluster_nodes {{ pillar['rabbitmq']['cluster_nodes'] }}
        /opt/seagate/eos/hare/bin/consul kv put rabbitmq/erlang_cookie {{ pillar['rabbitmq']['erlang_cookie'] }}

Add common config - BMC to Consul:
  cmd.run:
    - name: |
{% for node in pillar['cluster']['node_list'] %}
        /opt/seagate/eos/hare/bin/consul kv put bmc/eosnode-1/ip {{ pillar['cluster'][node]['bmc']['ip'] }}
        /opt/seagate/eos/hare/bin/consul kv put bmc/eosnode-1/user {{ pillar['cluster'][node]['bmc']['user'] }}
        /opt/seagate/eos/hare/bin/consul kv put bmc/eosnode-1/secret {{ pillar['cluster'][node]['bmc']['secret'] }}
{% endfor %}

Add common config - storage enclosure to Consul:
  cmd.run:
    - name: |
        /opt/seagate/eos/hare/bin/consul kv put storage_enclosure/controller/primary_mc/ip {{ pillar['storage_enclosure']['controller']['primary_mc']['ip'] }}
        /opt/seagate/eos/hare/bin/consul kv put storage_enclosure/controller/primary_mc/port {{ pillar['storage_enclosure']['controller']['primary_mc']['port'] }}
        /opt/seagate/eos/hare/bin/consul kv put storage_enclosure/controller/secondary_mc/ip {{ pillar['storage_enclosure']['controller']['secondary_mc']['ip'] }}
        /opt/seagate/eos/hare/bin/consul kv put storage_enclosure/controller/secondary_mc/port {{ pillar['storage_enclosure']['controller']['secondary_mc']['port'] }}
        /opt/seagate/eos/hare/bin/consul kv put storage_enclosure/controller/user {{ pillar['storage_enclosure']['controller']['user'] }}
        /opt/seagate/eos/hare/bin/consul kv put storage_enclosure/controller/password {{ pillar['storage_enclosure']['controller']['secret'] }}
{% else %}
Consul not applicable on secondary:
  test.show_notification:
    - text: Consul config updates are applicable only on primary node and not on secondary node.
{% endif %}

Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:post_install')

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:config')

{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Run Health Schema on minion:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n --path "/tmp/"

# run health schema on master for both node and enclosure and for minion only for node health.
# Run Health Schema on master:
#   cmd.run:
#     - name: /opt/seagate/eos/sspl/lib/resource_health_view -n -e --path "/tmp/"

{% if pillar['cluster']['type'] == 'ees' %}
Merge healthschema:
  module.run:
    - sspl.health_map_schema:
      - file_path: "/tmp/resource_health_view.json"
{% endif %}
{% else %}
Run Health Schema on minion:
  cmd.run:
    - name: /opt/seagate/eos/sspl/lib/resource_health_view -n --path "/tmp/"
{% endif %}
 
Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:init')
