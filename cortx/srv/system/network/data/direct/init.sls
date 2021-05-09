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

{#{% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}#}
# Update roaming IPs in cluster.sls pillar:
#   module.run:
#     - cluster.nw_roaming_ip: []
#     - saltutil.refresh_pillar: []
{#{% endif %}#}

Private data network configuration:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['data']['private_interfaces'][0] }}
    - enabled: True
    - device: {{ pillar['cluster'][node]['network']['data']['private_interfaces'][0] }}
    - type: eth
    # - onboot: yes             # [WARNING ] The 'onboot' option is controlled by the 'enabled' option.
    - defroute: no
    - nm_controlled: no
    - peerdns: no
    - userctl: no
    - prefix: 24
{% if pillar['cluster'][node]['network']['data']['private_ip'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data']['private_ip'] }}
    - mtu: {{ pillar['cluster'][node]['network']['data']['mtu'] }}
{%- else %}
    - proto: dhcp
{%- endif %}
