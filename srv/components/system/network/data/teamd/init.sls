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

# NOTE: Requires salt version 3002.2+
{% if "3002" not in salt["test.version"]() %}
Raise version mismatch exception:
  test.fail_without_changes:
    - name: "Salt version is less than required 3002.x version."
{% endif %}

{% set node = grains['id'] %}
Install teamd:
  pkg.installed:
    - name: teamd

Create data0 interface file:
    network.managed:
    - name: data0
    # - device: data0
    - type: team
    - enabled: True
    - nm_controlled: no
    # - onboot: yes             # [WARNING ] The 'onboot' option is controlled by the 'enabled' option.
    - userctl: no
    - defroute: no
    {% if pillar['cluster'][node]['network']['data']['public_ip'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['data']['public_ip'] }}
    - mtu: 9000
    {%- else %}
    - proto: dhcp
    {%- endif %}
    {% if pillar['cluster'][node]['network']['data']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data']['netmask'] }}
    {%- endif %}
    {% if pillar['cluster'][node]['network']['data']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['data']['gateway'] }}
    {% endif %}
    - team_config:
        runner:
          hwaddr_policy: by_active
          name: activebackup
          link_watch:
            name: ethtool

{% for interface in pillar['cluster'][node]['network']['data']['interfaces'] %}
{{ interface }}:
    network.managed:
    - name: {{ interface }}
    # - device:  {{ interface }}
    - type: teamport
    - team_master: data0
    - team_port_config:
        prio: 100
{% endfor %}
