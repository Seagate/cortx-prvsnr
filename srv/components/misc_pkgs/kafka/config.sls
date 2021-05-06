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


{% set node_ids = {} %}
{% set node_hosts = [] %}
{% set server_nodes = [] %}
{% for node in pillar['cluster'].keys() %}
{% if "srvnode-" in node %}
{% do server_nodes.append(node) %}
{% endif %}
{% endfor %}
{% for node in server_nodes %}
    {% set x = node_ids.update({node:loop.index}) %}
    {% set y = node_hosts.append( pillar['cluster'][node]['network']['data']['private_fqdn'] +
      ":" +
      (pillar['cortx']['software']['zookeeper']['client_port'] | string)
    ) %}
{% endfor %}

Update zoopkeeper cofig:
  file.managed:
    - name: /opt/kafka/config/zookeeper.properties
    - source: salt://components/misc_pkgs/kafka/files/zookeeper.properties
    - template: jinja
    - backup: '.bak'
    - user: kafka
    - group: kafka
    - mode: 644

Update permissions for datadir:
  file.directory:
    - name: /var/lib/zookeeper
    - user: kafka
    - group: kafka
    - dir_mode: 755
    - makedirs: True
    - recurse:
      - user
      - group
      - mode

Update permissions for datalogdir:
  file.directory:
    - name: /var/log/zookeeper
    - user: kafka
    - group: kafka
    - makedirs: True
    - dir_mode: 755
    - recurse:
      - user
      - group
      - mode

Create zookeeper id:
  file.append:
    - name: /var/lib/zookeeper/myid
    - text: {{ node_ids[grains['id']] }}
    - makedirs: True
    - user: kafka
    - group: kafka
    - mode: 644

Update broker_id in kafka config:
  file.replace:
    - name: /opt/kafka/config/server.properties
    - pattern: ^broker.id=.*
    - repl: broker.id={{ node_ids[grains['id']] }}
    - append_if_not_found: True
    - backup: '.bak'

Update log_dir in kafka config:
  file.replace:
    - name: /opt/kafka/config/server.properties
    - pattern: ^log.dirs=.*
    - repl: log.dirs=/var/log/kafka
    - append_if_not_found: True

update listner in kafka config:
  file.replace:
    - name: /opt/kafka/config/server.properties
    - pattern: ^#listeners=.*
    - repl: listeners=PLAINTEXT://{{pillar['cluster'][grains['id']]['network']['data']['private_fqdn']}}:{{pillar['cortx']['software']['kafka']['port']}}
    - append_if_not_found: True

Update connections in kafka config:
  file.replace:
    - name: /opt/kafka/config/server.properties
    - pattern: ^zookeeper.connect=.*
    - repl: zookeeper.connect={{ node_hosts|join(',')}}
    - append_if_not_found: True
