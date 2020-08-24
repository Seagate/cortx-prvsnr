#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

{% set node = grains['id'] %}
Ensure bonding config for data bond:
  file.managed:
    - name: /etc/modprobe.d/bonding.conf
    - contents: options bonding max_bonds=0

# Setup network for data interfaces
{% for iface in pillar['cluster'][node]['network']['data_nw']['iface'] %}
{{ iface }}:
  network.managed:
    - device: {{ iface }}
    - enabled: True
    - type: slave
    - master: data0
    - requires_in:
      - Setup data0 bonding
    - watch_in:
      - Shutdown {{ iface }}

Shutdown {{ iface }}:
  cmd.run:
    - name: ifdown {{ iface }}
    - onlyif: '[ "up" == "$(cat /sys/class/net/{{iface}}/operstate)" ]'
{% endfor %}

Setup data0 bonding:
  network.managed:
    - name: data0
    - type: bond
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - mtu: 9000
    - defroute: no
    - mode: 802.3ad
    - miimon: 100
    - lacp_rate: fast
    - xmit_hash_policy: layer2+3
{% if pillar['cluster'][node]['network']['data_nw']['public_ip_addr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data_nw']['public_ip_addr'] }}
{%- else %}
    - proto: dhcp
{%- endif %}
{% if pillar['cluster'][node]['network']['data_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data_nw']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['data_nw']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['data_nw']['gateway'] }}
{% endif %}
