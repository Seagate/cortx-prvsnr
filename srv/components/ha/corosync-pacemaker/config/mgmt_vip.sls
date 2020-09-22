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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

{% if 'primary' in grains['roles'] 
  and pillar['cluster']['mgmt_vip'] %}
Update Management VIP:
  cmd.run:
    - name: pcs resource update kibana-vip ip={{ pillar['cluster']['mgmt_vip'] }}

{% else %}

No Management VIP application:
  test.show_notification:
    - text: "Management VIP application only applies to primary node. Either this is not a primary node or value of Management Network VIP is missing in cluster pillar."

{% endif %}
