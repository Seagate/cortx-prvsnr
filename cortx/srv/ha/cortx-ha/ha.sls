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
include:
  - ha.cortx-ha.install
  - ha.iostack-ha.prepare

Run cortx-ha HA setup:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:ha')
    - require:
      - Install cortx-ha
      - Render ha input params template
{% else %}
No HA setup on secondary node:
  test.show_notification:
    - text: "HA setup applies to primary node. There's no execution on secondary node"
{% endif %}
