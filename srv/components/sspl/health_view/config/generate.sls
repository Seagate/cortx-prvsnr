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

{% if not ("replace_node" in pillar["cluster"]
  and grains['id'] == pillar["cluster"]["replace_node"]["minion_id"]) %}
# Should not be run for replaced node
include:
  - components.sspl.config.commons
{% endif %}

{% set enclosure = '' %}
{% if "primary" in pillar["cluster"][grains["id"]]["roles"] and 'physical' in grains['virtual'] %}
# run health schema on salt-master for both node and enclosure;
# on salt-minion only for node health.
{% set enclosure = '-e' %}
{% endif %}
Run Resource Health View:
  cmd.run:
    - name: /usr/bin/resource_health_view -n {{ enclosure }} --path {{ pillar['sspl']['health_map_path'] }}
{% if not ("replace_node" in pillar["cluster"]
  and grains['id'] == pillar["cluster"]["replace_node"]["minion_id"]) %}
# Should not be run for replaced node
    - require:
      - Add common config - system information to Consul
      - Add common config - rabbitmq cluster to Consul
      - Add common config - BMC to Consul
      - Add common config - storage enclosure to Consul
{% endif %}
