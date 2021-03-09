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

# Setup network for data interfaces
Public data network configuration:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['data']['public_interfaces'][0] }}
    - device: {{ pillar['cluster'][node]['network']['data']['public_interfaces'][0] }}
    - type: eth
    - enabled: True
    - nm_controlled: no
    # - onboot: yes             # [WARNING ] The 'onboot' option is controlled by the 'enabled' option.
    - userctl: no
    - defroute: no
{% if pillar['cluster'][node]['network']['data']['public_ip'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data']['public_ip'] }}
    - mtu: {{ pillar['cluster'][node]['network']['data']['mtu'] }}
{% if pillar['cluster'][node]['network']['data']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['data']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['data']['gateway'] }}
{% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

