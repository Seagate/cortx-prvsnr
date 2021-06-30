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

{% set mgmt_vip = pillar['cluster']['mgmt_vip'] -%}
{% if mgmt_vip %}
{% if not salt['network.ping'](mgmt_vip, return_boolean=True, timeout=1) %}
{% set node = grains['id'] %}
{% set mgmt_if = pillar['cluster'][node]['network']['mgmt']['interfaces'][0] %}
{% set mgmt_netmask = grains['ip4_netmask'][mgmt_if] %}

IP alias of mgmt_vip with {{ mgmt_if }}:
  cmd.run:
    - name: ip a add {{mgmt_vip}}/{{mgmt_netmask}} dev {{mgmt_if}}

{% else %}

IP already in use:
  test.show_notification:
    - text: "Specified management VIP {{ mgmt_vip }} is already in use. So unable to create alias."

{% endif %}

{% endif %}

