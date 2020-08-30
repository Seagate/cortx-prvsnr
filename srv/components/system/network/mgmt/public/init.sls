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

{% set node = grains['id'] %}
{% if pillar['cluster'][node]['network']['mgmt_nw']['public_ip_addr']
    and not pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway'] %}

Gateway not provided:
  test.fail_with_changes:
    - name: Static IP's for public management network requires a valid gateway. Provide a valid gateway value in cluster.sls and retry this state.

{% else %}

# Setup network for data interfaces
Public direct network:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['mgmt_nw']['iface'][0] }}
    - device: {{ pillar['cluster'][node]['network']['mgmt_nw']['iface'][0] }}
    - type: eth
    - enabled: True
    - nm_controlled: no
    - onboot: yes
    - userctl: no
    - defroute: yes
{% if pillar['cluster'][node]['network']['mgmt_nw']['public_ip_addr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['mgmt_nw']['public_ip_addr'] }}
    - mtu: 1500
{%- else %}
    - proto: dhcp
{%- endif %}
{% if pillar['cluster'][node]['network']['mgmt_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['mgmt_nw']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['mgmt_nw']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway'] }}
{% endif %}
{% endif %} # Gateway check end
