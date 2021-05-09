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
  # Remove Management stack
  - csm.teardown
  - sspl.teardown
  # Remove IO Stack
  - ha.iostack-ha.teardown
  - hare.teardown
  - s3server.teardown
  - motr.teardown
  # Remove pre-reqs
  - misc_pkgs.lustre.teardown
  - misc_pkgs.statsd.teardown
  - misc_pkgs.rabbitmq.teardown
  - misc_pkgs.openldap.teardown
  - misc_pkgs.nodejs.teardown
  - misc_pkgs.kibana.teardown
  - misc_pkgs.elasticsearch.teardown
  - ha.haproxy.teardown
  - ha.corosync-pacemaker.teardown
  - misc_pkgs.build_ssl_cert_rpms.teardown
  - system.storage.teardown
  # - system.mlnx_driver.teardown
  - system.chrony.teardown
  - system.logrotate.teardown
  - system.firewall.teardown
  - system.teardown
