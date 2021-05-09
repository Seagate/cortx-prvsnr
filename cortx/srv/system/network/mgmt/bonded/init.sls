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
{%- if (pillar['cluster'][node]['network']['mgmt']['public_ip']) and (not pillar['cluster'][node]['network']['mgmt']['gateway']) %}
Management network config failure:
  test.fail_without_changes:
    - name: Static network configuration in absense of Gateway IP would result in node inaccessibility.
{%- endif %}

Ensure bonding config for management bond:
  file.managed:
    - name: /etc/modprobe.d/bonding.conf
    - contents: options bonding max_bonds=0

# Setup network for management interfaces
{% for interface in pillar['cluster'][node]['network']['mgmt']['interfaces'] %}
{{ interface }}:
  network.managed:
    - device: {{ interface }}
    - enabled: True
    - type: slave
    - master: mgmt0

Shutdown {{ interface }}:
  cmd.run:
    - name: ifdown {{ interface }}
    - onlyif: '[ "up" == "$(cat /sys/class/net/{{interface}}/operstate)" ]'
{% endfor %}

Setup mgmt0 bonding:
  network.managed:
    - name: mgmt0
    - type: bond
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - defroute: yes
    # - slaves: em1 em2
    - mode: active-backup
    - miimon: 100
{% if pillar['cluster'][node]['network']['mgmt']['public_ip'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['mgmt']['public_ip'] }}
    - mtu: {{ pillar['cluster'][node]['network']['mgmt']['mtu'] }}
{% if pillar['cluster'][node]['network']['data']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['data']['gateway'] %}
    - gateway: {{ pillar['cluster'][node]['network']['mgmt']['gateway'] }}
{% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

include:
  - system.network.config
