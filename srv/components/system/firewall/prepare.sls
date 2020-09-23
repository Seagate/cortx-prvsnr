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

#To enable firewall IP table has to be disabled
Disable iptables:
  service.dead:
    - name: iptables
    - enable: False

Disable ip6tables:
  service.dead:
    - name: ip6tables
    - enable: False

Disable ebtables:
  service.dead:
    - name: ebtables
    - enable: False

# Mask the above to ensure they are never started
Mask iptables:
  service.masked:
    - name: iptables

Mask ip6tables:
  service.masked:
    - name: ip6tables

Mask ebtables:
  service.masked:
    - name: ebtables
