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

Ensure driver config is removed:
  file.absent:
    - name: /opt/cos/conf/driver.conf

Ensure controller config is removed:
  file.absent:
    - name: /opt/cos/conf/controller.conf

Ensure cosbench directory is removed:
  file.absent:
    - name: /opt/cos

Close driver port:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: DROP
    - protocol: tcp
    - match: tcp
    - dport: 18088
    - connstate: NEW
    - family: ipv4
    - save: True

Close controller port:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: DROP
    - protocol: tcp
    - match: tcp
    - dport: 19088
    - family: ipv4
    - save: True
