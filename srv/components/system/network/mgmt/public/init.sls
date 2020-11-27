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

{% set node = grains['id'] %}
{% if pillar['cluster'][node]['network']['mgmt_nw']['public_ip_addr']
    and not pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway'] %}

Gateway not provided:
  test.fail_with_changes:
    - name: Static IP's for public management network requires a valid gateway. Provide a valid gateway value in cluster.sls and retry this state.

{% else %}

{% set mgmt_if = pillar['cluster'][node]['network']['mgmt_nw']['iface'][0] %}
# Setup network for data interfaces
Public direct network:
  network.managed:
    - name: {{ mgmt_if }}
    - device: {{ mgmt_if }}
    - type: eth
    - enabled: True
    - nm_controlled: no
    # - onboot: yes             # [WARNING ] The 'onboot' option is controlled by the 'enabled' option.
    - userctl: no
    - hwaddr: {{ grains['hwaddr_interfaces'][mgmt_if] }}
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
