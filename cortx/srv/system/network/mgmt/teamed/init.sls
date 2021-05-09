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
{% if pillar['cluster'][node]['network']['mgmt']['public_ip']
    and not pillar['cluster'][node]['network']['mgmt']['gateway'] %}

Gateway not provided:
  test.fail_with_changes:
    - name: Static IP's for public management network requires a valid gateway. Provide a valid gateway value in cluster.sls and retry this state.

{% else %}

Install teamd:
  pkg.installed:
    - name: teamd

Create mgmt0 interface file:
    network.managed:
    - name: mgmt0
    # - device: mgmt0
    - type: team
    - enabled: True
    - nm_controlled: no
    # - onboot: yes             # [WARNING ] The 'onboot' option is controlled by the 'enabled' option.
    - userctl: no
    - defroute: yes
    {% if pillar['cluster'][node]['network']['mgmt']['public_ip'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['mgmt']['public_ip'] }}
    - mtu: 1500
    {%- else %}
    - proto: dhcp
    {%- endif %}
    {% if pillar['cluster'][node]['network']['mgmt']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['mgmt']['netmask'] }}
    {%- endif %}
    {% if pillar['cluster'][node]['network']['mgmt']['gateway'] %}
    - gateway: {{ pillar['cluster'][node]['network']['mgmt']['gateway'] }}
    {% endif %}
    - team_config:
        runner:
          hwaddr_policy: by_active
          name: activebackup
          link_watch:
            name: ethtool

{% for interface in pillar['cluster'][node]['network']['mgmt']['interfaces'] %}
{{ interface }}:
    network.managed:
    - name: {{ interface }}
    # - device:  {{ interface }}
    - type: teamport
    - team_master: mgmt0
    - team_port_config:
        prio: 100
{% endfor %}

{% endif %} # Gateway check end
