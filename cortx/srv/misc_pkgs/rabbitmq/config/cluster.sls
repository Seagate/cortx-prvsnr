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

{% set server_nodes = [ ] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
include:
  - misc_pkgs.rabbitmq.start

Start rabbitmq app and join cluster if available:
  cmd.run:
    - name: |
        rabbitmqctl start_app
        rabbitmqctl stop_app
        {#% for node in (salt['saltutil.runner']("manage.up") | difference(grains['id'])) %#}
        {% for node in (server_nodes | difference(grains['id'])) %}
        rabbitmqctl join_cluster rabbit@{{ node }} || true
        {% endfor %}
        rabbitmqctl start_app
        rabbitmqctl set_cluster_name rabbitmq-cluster
    - require:
      - Start RabbitMQ service
