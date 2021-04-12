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

{% set kafka_version = pillar['commons']['version']['kafka'] %}

{%- set node_ids = {} -%}
{%- set node_hosts = [] -%}
{% set server_nodes = [] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node) %}
{% endif -%}
{% endfor -%}
{%- for node in server_nodes -%}
    {%- set x=node_ids.update({node:loop.index}) -%}
    {%- set y=node_hosts.append(pillar['cluster'][node]['network']['data']['private_fqdn'] + ":9092") -%}
{%- endfor -%}

Update zoopkeeper cofig:
  file.managed:
    - name: /opt/kafka/kafka_{{ kafka_version }}/config/zookeeper.properties
    - source: salt://components/misc_pkgs/kafka/files/zookeeper.properties
    - template: jinja
    - backup: '.bak'

Create zookeeper id:
  file.append:
   - name: /var/lib/zookeeper/myid
   - text: {{ node_ids[grains['id']] }}
   - makedirs: True

Update broker_id in kafka config:
  file.replace:
    - name: /opt/kafka/kafka_{{ kafka_version }}/config/server.properties
    - pattern: ^broker.id=.*
    - repl: broker.id={{ node_ids[grains['id']] }}
    - append_if_not_found: True
    - backup: '.bak'

Update log_dir in kafka config:
  file.replace:
    - name: /opt/kafka/kafka_{{ kafka_version }}/config/server.properties
    - pattern: ^log.dirs=.*
    - repl: log.dirs=/var/log/kafka
    - append_if_not_found: True

Update connections in kafka config:
  file.replace:
    - name: /opt/kafka/kafka_{{ kafka_version }}/config/server.properties
    - pattern: ^zookeeper.connect=.*
    - repl: zookeeper.connect={{ node_hosts|join(',')}}
    - append_if_not_found: True
