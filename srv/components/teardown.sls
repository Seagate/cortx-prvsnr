#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

include:
  # Remove Management stack
  - components.csm.teardown
  - components.sspl.teardown
  # Remove IO Stack
  - components.ha.ees_ha.teardown
  - components.hare.teardown
  - components.s3server.teardown
  - components.motr.teardown
  # Remove pre-reqs
  - components.misc_pkgs.lustre.teardown
  - components.misc_pkgs.statsd.teardown
  - components.misc_pkgs.rabbitmq.teardown
  - components.misc_pkgs.openldap.teardown
  - components.misc_pkgs.nodejs.teardown
  - components.misc_pkgs.kibana.teardown
  - components.misc_pkgs.elasticsearch.teardown
  - components.ha.haproxy.teardown
  - components.ha.corosync-pacemaker.teardown
  - components.misc_pkgs.build_ssl_cert_rpms.teardown
  - components.system.storage.teardown
  # - components.system.mlnx_driver.teardown
  - components.system.chrony.teardown
  - components.system.logrotate.teardown
  - components.system.firewall.teardown
  - components.system.teardown
