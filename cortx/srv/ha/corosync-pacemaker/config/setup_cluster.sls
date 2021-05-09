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

# This state file is ignored if run on replacement node
# replacement node check & priamry node check
{% set server_nodes = [ ] %}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
{% if not salt["environ.get"]('REPLACEMENT_NODE')
  and 'primary' in grains['roles'] %}
Setup Cluster:
  pcs.cluster_setup:
    - nodes:
      {%- for node_id in server_nodes %}
      - {{ node_id }}
      {%- endfor %}
    - pcsclustername: {{ pillar['cortx']['software']['corosync-pacemaker']['cluster_name'] }}
    - extra_args:
      - '--start'
      - '--enable'
      - '--force'

Ignore the Quorum Policy:
  pcs.prop_has_value:
    - prop: no-quorum-policy
    - value: ignore

{% set stonith_enabled = 'false' %}
{% if pillar['cluster'][grains['id']]['bmc']['ip']
  and "physical" in grains['virtual'] %}
{% set stonith_enabled = 'true' %}
{% endif %}

Enable STONITH:
  pcs.prop_has_value:
    - prop: stonith-enabled
    - value: {{ stonith_enabled }}     # Set only if BMC IP is specified

{% else %}            # Check for is node primary

No Cluster Setup:
  test.show_notification:
    - text: "Cluster setup applies only to primary node. There's no Cluster setup operation on secondary node"

{%- endif -%}         # Check: Is node primary & is replacement node
