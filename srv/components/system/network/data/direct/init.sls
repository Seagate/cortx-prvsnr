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

{#{% if pillar['cluster'][grains['id']]['is_primary'] %}#}
# Update roaming IPs in cluster.sls pillar:
#   module.run:
#     - cluster.nw_roaming_ip: []
#     - saltutil.refresh_pillar: []
{#{% endif %}#}

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
    {% if "physical" in grains['virtual'] %}
    - mtu: 9000
    {% else %}
    - mtu: 1500
    {% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}
