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
include:
  - components.system.prepare

{#{% if pillar['cluster'][grains['id']]['is_primary'] %}#}
# Update roaming IPs in cluster.sls pillar:
#   module.run:
#     - cluster.nw_roaming_ip: []
#     - saltutil.refresh_pillar: []
{#{% endif %}#}

# Setup network for data interfaces
Public direct network:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['data_nw']['iface'][0] }}
    - device: {{ pillar['cluster'][node]['network']['data_nw']['iface'][0] }}
    - type: eth
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - onboot: yes
    - userctl: no
    - defroute: no
{% if pillar['cluster'][node]['network']['data_nw']['ipaddr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data_nw']['ipaddr'] }}
    - mtu: 9000
{% if pillar['cluster'][node]['network']['data_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data_nw']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['data_nw']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['data_nw']['gateway'] }}
{% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

{#{% set pvt_nw = pillar['cluster']['pvt_data_nw_addr'] %}#}
{#{% set pvt_ip = ("{0}.{1}").format('.'.join(pvt_nw.split('.')[:3]), grains['id'].split('-')[1]) %}#}
Private direct network:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['data_nw']['iface'][1] }}
    - enabled: True
    - device: {{ pillar['cluster'][node]['network']['data_nw']['iface'][1] }}
    - type: eth
    - onboot: yes
    - defroute: no
    - nm_controlled: no
    - peerdns: no
    - userctl: no
    - prefix: 24
{% if pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] }}
    - mtu: 9000
{%- else %}
    - proto: dhcp
{%- endif %}
