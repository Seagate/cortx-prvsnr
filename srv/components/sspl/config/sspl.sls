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
  - components.sspl.install
{% if not ("replace_node" in pillar["cluster"]
  and grains['id'] == pillar["cluster"]["replace_node"]["minion_id"]) %}
# Should not be executed for replaced node
  - components.sspl.config.commons
  - components.sspl.health_view.prepare
  - components.sspl.health_view.config
{% endif %}

Stage - Post Install SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/sspl/conf/setup.yaml', 'sspl:post_install')
    - failhard: True
    - require:
      - Install cortx-sspl

Stage - Configure SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/sspl/conf/setup.yaml', 'sspl:config')
    - failhard: True
    - require:
      - Stage - Post Install SSPL
{% if not ("replace_node" in pillar["cluster"]
  and grains['id'] == pillar["cluster"]["replace_node"]["minion_id"]) %}
# Should not be executed for replaced node
      - Add common config - system information to Consul
      - Add common config - rabbitmq cluster to Consul
      - Add common config - BMC to Consul
      - Add common config - storage enclosure to Consul
{% endif %}
    - order: 5

{% if not ("replace_node" in pillar["cluster"]
  and grains['id'] == pillar["cluster"]["replace_node"]["minion_id"]) %}
# Should not be executed for replaced node
Stage - Initialize SSPL:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/sspl/conf/setup.yaml', 'sspl:init')
    - failhard: True
    - require:
      - Copy setup.yaml to /opt/seagate/health_view/conf
      - Run Resource Health View
      - Stage - Configure SSPL
    - order: 10
{% endif %}
