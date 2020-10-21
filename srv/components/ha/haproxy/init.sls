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

include:
  - components.misc_pkgs.rsyslog
  - components.ha.haproxy.prepare
  - components.ha.haproxy.install
  - components.ha.haproxy.config
  # Disable start to be explicitly started later
  # Requires Cluster_IP to be set by corosync-pacemaker before start in HW
  # - components.ha.haproxy.start
  # - components.ha.haproxy.sanity_check
  - components.ha.haproxy.stop
