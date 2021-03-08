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
{% if pillar['cluster'][node]['network']['mgmt']['interfaces'][1] is defined %}
# Check if the extra NIC is provided in cluster pillar
# for configuration as service port
  {%- if "srvnode-1" in grains['id'] %}
  # Apply only on srvnode-1

Service port configuration on embedded NIC:
  network.managed:
    - name: {{ pillar['cluster'][node]['network']['mgmt']['interfaces'][1] }}
    - device: {{ pillar['cluster'][node]['network']['mgmt']['interfaces'][1] }}
    - type: eth
    - enabled: True
    - onboot: yes
    - userctl: no
    - nm_controlled: no
    # Never add this NIC to default route
    - defroute: no
    - mtu: {{ pillar['cluster'][node]['network']['mgmt']['mtu'] }}
    # Static IP address
    - proto: none
    - ipaddr: 10.100.100.100
    # Netmask/prefix 24
    # - prefix: 24      # Not supported by Salt  
    - netmask: 255.255.255.0

  {% endif %}
{% else %}
Network interface for service port not specified:
  test.show_notification:
    - text: "A dedicated network interface for service port not specified in cluster pillar. Please contact Seagate support to help specify a second interface in addtion to {{ pillar['cluster'][node]['network']['mgmt']['interfaces'][0] }} and re-run this state formula."
{% endif %}
