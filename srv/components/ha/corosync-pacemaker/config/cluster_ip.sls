#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

{% if "primary" in grains['roles'] 
  and pillar['cluster']['cluster_ip'] -%}

{% if (0 == salt['cmd.retcode']('command -v pcs')) 
  and (0 == salt['cmd.retcode']('pcs resource show ClusterIP-clone')) -%}

Update ClusterIP:
  cmd.run:
    - name: pcs resource update ClusterIP ip={{ pillar['cluster']['cluster_ip'] }}
    - onlyif: pcs resource show ClusterIP

{% else %}  # Is pcs installed & ClusterIP exists

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] -%}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
{%- endif -%}

Setup ClusterIP resouce:
  cmd.run:
    - name: pcs resource create ClusterIP ocf:heartbeat:IPaddr2 ip={{ pillar['cluster']['cluster_ip'] }} mac=$(echo "01:00:5e:`echo {{ grains['hwaddr_interfaces'][data_if] }} | cut -d ":" -f 1-3`") nic={{ data_if }} op monitor interval=30s

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

{% endif %} # Is pcs installed & ClusterIP exists

{% else %}  # Is node primary

No Cluster IP application:
  test.show_notification:
    - text: "Cluster IP application applies only to primary node. Either this is not a primary node or value of Cluster IP is missing in cluster pillar."

{% endif %}  # Is node primary
