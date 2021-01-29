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

{% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}
Setup UDS HA:
  cmd.run:
    - name: /opt/seagate/cortx/ha/conf/script/build-ha-uds
{% else %}
No post install for UDS:
  test.show_notification:
    - text: "Post install for UDS only applies to primary node. There's no execution on secondary node"
{% endif %}
