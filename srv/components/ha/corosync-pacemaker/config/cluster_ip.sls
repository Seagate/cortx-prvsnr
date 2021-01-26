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

{% if "primary" in grains['roles'] 
  and pillar['cluster']['cluster_ip']
  and "physical" in grains['virtual']
%}

{% if (0 == salt['cmd.retcode']('command -v pcs')) %}

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] -%}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data']['public_interfaces'][0] -%}
{%- endif -%}

{% if (0 == salt['cmd.retcode']('pcs resource show ClusterIP-clone')) %}

Update ClusterIP:
  cmd.run:
    - name: pcs resource update ClusterIP ip={{ pillar['cluster']['cluster_ip'] }} cidr_netmask=$(ip addr show {{ data_if }} | grep -m 1 "inet\b" | awk '{print $2}' | cut -d "/" -f2) op monitor interval=30s
    - onlyif: pcs resource show ClusterIP

{% else %}  # Is pcs installed & ClusterIP exists

Setup ClusterIP resouce:
  cmd.run:
    - name: pcs resource create ClusterIP ocf:heartbeat:IPaddr2 ip={{ pillar['cluster']['cluster_ip'] }} mac=$(echo "01:00:5e:`echo {{ grains['hwaddr_interfaces'][data_if] }} | cut -d ":" -f 1-3`") nic={{ data_if }} cidr_netmask=$(ip addr show {{ data_if }} | grep -m 1 "inet\b" | awk '{print $2}' | cut -d "/" -f2) op monitor interval=30s

Add stickiness metadata to ClusterIP resource:
  cmd.run:
    - name: pcs resource meta ClusterIP resource-stickiness=0
    - require:
      - Setup ClusterIP resouce

Clone ClusterIP:
  cmd.run:
    - name: pcs resource clone ClusterIP clusterip_hash=sourceip-sourceport clone-max=2 clone-node-max=2 globally-unique=true priority=1
    # priority=1 above ensures that ClusterIP-clone is distributed across nodes.
    - requries:
      - Setup ClusterIP resouce
{% endif %} # ClusterIP exists
{% endif %} # Is pcs installed

{% else %}  # Is node primary

No Cluster IP application:
  test.show_notification:
    - text: "Cluster IP application applies only to primary node. Either this is not a primary node or value of Cluster IP is missing in cluster pillar."

{% endif %}  # Is node primary
