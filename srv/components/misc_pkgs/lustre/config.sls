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

{% if 'lo' in pillar['cluster'][grains['id']]['network']['data_nw'] %}
Update lnet config file:
  test.fail_without_changes:
    - name: LNet doesn't support loopback network interface. Config dropped.

{% else %}
{%- if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] -%}
{%- endif -%}

Update lnet config file:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
{% if salt['cmd.run']('lspci -d"15b3:*"|grep Mellanox') %}
      - options lnet networks=o2ib({{ data_if }})  config_on_load=1  lnet_peer_discovery_disabled=1
{% else %}
      - options lnet networks=tcp({{ data_if }})  config_on_load=1  lnet_peer_discovery_disabled=1
{% endif %}
    - user: root
    - group: root

{% endif %}
