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

include:
  - components.sspl.teardown.sspl

{% set consul_service = 'hare-consul-agent-c1' if "primary" == grains['roles'] else 'hare-consul-agent-c2' %}
{% if salt['service.status'](consul_service, false) %}
Delete common config - system information to Consul:
  cmd.run:
    - name: |
        consul kv delete system_information/operating_system
        consul kv delete system_information/kernel_version
        consul kv delete system_information/product
        consul kv delete system_information/site_id
        consul kv delete system_information/rack_id
        consul kv delete system_information/cluster_id
        consul kv delete system_information/{{ grains['id'] }}/node_id
        consul kv delete system_information/syslog_host
        consul kv delete system_information/syslog_port
        consul kv delete system_information/healthmappath
    - require:
      - Delete sspl checkpoint flag

Delete common config - rabbitmq cluster to Consul:
  cmd.run:
    - name: |
        consul kv delete rabbitmq/cluster_nodes
        consul kv delete rabbitmq/erlang_cookie
    - require:
      - Delete sspl checkpoint flag

{% server_nodes = [node for node in pillar['cluster'].keys() if "srvnode_" in node] %}
Delete common config - BMC to Consul:
  cmd.run:
    - name: |
    {% for node_id in server_nodes %}
        consul kv delete bmc/{{ node_id }}/ip
        consul kv delete bmc/{{ node_id }}/user
        consul kv delete bmc/{{ node_id }}/secret['secret']
    {% endfor %}
    - require:
      - Delete sspl checkpoint flag

{% enclosures = [enclosure for enclosure in pillar['storage'].keys() if "enclosure_" in enclosure] %}
Delete common config - storage enclosure to Consul:
  cmd.run:
    - name: |
{% for enclosure_id in enclosures %}
        consul kv delete storage/{{ enclosure_id }}/primary/ip
        consul kv delete storage/{{ enclosure_id }}/primary/port
        consul kv delete storage/{{ enclosure_id }}/secondary/ip
        consul kv delete storage/{{ enclosure_id }}/secondary/port
        consul kv delete storage/{{ enclosure_id }}/user
        consul kv delete storage/{{ enclosure_id }}/password
{% endfor %}
    - require:
      - Delete sspl checkpoint flag

{% else %}

Delete common config:
  test.show_notification:
    - text: "Consul service not running. Nothing to do."

{% endif %}
