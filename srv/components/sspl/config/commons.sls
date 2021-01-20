#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

Add common config - system information to Consul:
  cmd.run:
    - name: |
        consul kv put system_information/operating_system "$(cat /etc/system-release)"
        consul kv put system_information/kernel_version {{ grains['kernelrelease'] }}
        consul kv put system_information/product {{ pillar['cluster']['type'] }}
        consul kv put system_information/site_id 001
        consul kv put system_information/rack_id 001
        consul kv put system_information/cluster_id {{ grains['cluster_id'] }}
        consul kv put system_information/{{ grains['id'] }}/node_id {{ grains['node_id'] }}
        consul kv put system_information/syslog_host {{ pillar['rsyslog']['host'] }}
        consul kv put system_information/syslog_port {{ pillar['rsyslog']['port'] }}
        consul kv put system_information/healthmappath {{ pillar['sspl']['health_map_path'] + '/' + pillar['sspl']['health_map_file'] }}

Add common config - rabbitmq cluster to Consul:
  cmd.run:
    - name: |
        consul kv put rabbitmq/cluster_nodes {{ pillar['rabbitmq']['cluster_nodes'] }}
        consul kv put rabbitmq/erlang_cookie {{ pillar['rabbitmq']['erlang_cookie'] }}

{% server_nodes = [node for node in pillar['cluster'].keys() if "srvnode-" in node] %}
Add common config - BMC to Consul:
  cmd.run:
    - name: |
{% for node_id in server_nodes %}
        consul kv put bmc/{{ node_id }}/ip {{ pillar['cluster'][node_id]['bmc']['ip'] }}
        consul kv put bmc/{{ node_id }}/user {{ pillar['cluster'][node_id]['bmc']['user'] }}
        consul kv put bmc/{{ node_id }}/secret {{ pillar['cluster'][node_id]['bmc']['secret'] }}
{% endfor %}


{% enclosures = [enclosure for enclosure in pillar['storage'].keys() if "enclosure-" in enclosure] %}
Add common config - storage enclosure to Consul:
  cmd.run:
    - name: |
{% for enclosure_id in enclosures %}
        consul kv put storage/{{ enclosure_id }}/primary/ip {{ pillar['storage'][{{ enclosure_id }}]['controller']['primary']['ip'] }}
        consul kv put storage/{{ enclosure_id }}/primary/port {{ pillar['storage'][{{ enclosure_id }}]['controller']['primary']['port'] }}
        consul kv put storage/{{ enclosure_id }}/secondary/ip {{ pillar['storage'][{{ enclosure_id }}]['controller']['secondary']['ip'] }}
        consul kv put storage/{{ enclosure_id }}/secondary/port {{ pillar['storage'][{{ enclosure_id }}]['controller']['secondary']['port'] }}
        consul kv put storage/{{ enclosure_id }}/user {{ pillar['storage'][{{ enclosure_id }}]['controller']['user'] }}
        consul kv put storage/{{ enclosure_id }}/password {{ pillar['storage'][{{ enclosure_id }}]['controller']['secret'] }}
{% endfor %}
