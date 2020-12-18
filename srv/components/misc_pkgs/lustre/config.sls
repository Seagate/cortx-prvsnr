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

{% if 'lo' in pillar['cluster'][grains['id']]['network']['data_nw'] %}
Update lnet config file:
  test.fail_without_changes:
    - name: LNet doesn't support loopback network interface. Config dropped.

{% else %}
{%- if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- if pillar['cluster'][node]['network']['data_nw']['iface']|length > 1 %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] -%}
  {%- else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
  {%- endif %}
{%- endif -%}

Update lnet config file:
  file.managed:
    - name: /etc/modprobe.d/lnet.conf
    - contents:
{% if salt['cmd.run']('lspci -d"15b3:*"') %}
      - options lnet networks=o2ib({{ data_if }})  config_on_load=1  lnet_peer_discovery_disabled=1
{% else %}
      - options lnet networks=tcp({{ data_if }})  config_on_load=1  lnet_peer_discovery_disabled=1
{% endif %}
    - user: root
    - group: root

{% endif %}
